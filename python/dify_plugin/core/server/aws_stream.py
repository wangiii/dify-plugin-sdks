from collections.abc import Callable, Generator
import io
import json
from queue import Queue
import threading
from flask import Flask, Response, request
from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.stream.stream_reader import PluginInputStreamReader
from dify_plugin.stream.stream_writer import PluginOutputStreamWriter


class AWSLambdaStream(PluginOutputStreamWriter, PluginInputStreamReader):
    def __init__(self, port: int, max_single_connection_lifetime: int):
        """
        Initialize the AWSLambdaStream and wait for jobs
        """
        self.app = Flask(__name__)
        self.port = port
        self.max_single_connection_lifetime = max_single_connection_lifetime
        self.request_stream: dict[str, Queue] = {}
        self.request_stream_lock = threading.Lock()
        self.thread_stream: dict[int, Queue] = {}
        self.thread_stream_lock = threading.Lock()
        self.request_queue = Queue[tuple[dict, Callable[[Callable[[], None]], None]]]()

        # setup server
        self._serve()

    def _get_request_stream(self, plugin_request_id: str) -> Queue:
        """
        Get request stream
        """
        with self.request_stream_lock:
            if plugin_request_id not in self.request_stream:
                # create new queue
                self.request_stream[plugin_request_id] = Queue()

            return self.request_stream[plugin_request_id]

    def write(self, data: str):
        """
        Write data to http response
        """
        thread_id = threading.get_ident()
        if thread_id not in self.thread_stream:
            raise Exception("No stream found for the current thread")

        self.thread_stream[thread_id].put(data)

    def read(
        self,
    ) -> Generator[tuple[dict, Callable[[Callable[[], None]], None]], None, None]:
        """
        Read request from http server
        """
        while True:
            yield self.request_queue.get()

    def _serve(self):
        """
        Serve the request
        """

        @self.app.route("/response", methods=["GET"])
        def response():
            try:
                # get plugin_request_idw
                plugin_request_id = request.headers.get("x-dify-plugin-request-id")
                if not plugin_request_id:
                    raise Exception("x-dify-plugin-request-id not found in the header")

                # get queue
                queue = self._get_request_stream(plugin_request_id)

                def generator():
                    while True:
                        data = queue.get()
                        if data is None:
                            break
                        yield data

                return Response(generator(), mimetype="text/plain")
            except Exception as e:
                return str(e)

        @self.app.route("/invoke", methods=["POST"])
        def server():
            try:
                # get plugin_request_id
                plugin_request_id = request.headers.get("x-dify-plugin-request-id")
                if not plugin_request_id:
                    raise Exception("x-dify-plugin-request-id not found in the header")

                queue = self._get_request_stream(plugin_request_id)

                for data in io.TextIOWrapper(request.stream, encoding="utf-8"):
                    # check payload
                    data = json.loads(data)
                    if "session_id" not in data or not isinstance(
                        data["session_id"], str
                    ):
                        raise Exception("session_id not found in the payload")

                    if (
                        "event" not in data
                        or not isinstance(data["event"], str)
                        or data["event"] not in PluginInStream.Event
                    ):
                        raise Exception("event not found in the payload")

                    if "data" not in data or not isinstance(data["data"], dict):
                        raise Exception("data not found in the payload")

                    # put request to queue
                    self.request_queue.put((data, self._hijack_func(queue)))

                return Response("ok", mimetype="text/plain")
            except Exception as e:
                return str(e)
            finally:
                assert plugin_request_id
                queue.put(None)
                del self.request_stream[plugin_request_id]

    def _hijack_func(self, queue: Queue) -> Callable[[Callable[[], None]], None]:
        """
        Hijack the execution
        """

        def wrapper(executor: Callable[[], None]):
            # get current thread id
            thread_id = threading.get_ident()
            # set queue for the current thread
            self.thread_stream[thread_id] = queue

            # run process
            try:
                executor()
            except Exception as e:
                queue.put(str(e))

            # close the stream
            queue.put(None)

            # remove stream
            del self.thread_stream[thread_id]

        return wrapper

    def launch(self):
        """
        Launch server
        """
        threading.Thread(
            target=self.app.run, kwargs={"port": self.port, "threaded": True}
        ).start()
