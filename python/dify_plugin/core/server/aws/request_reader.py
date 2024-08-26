from queue import Queue
import threading
from typing import Generator
from flask import Flask, request
from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.core.server.__base.request_reader import RequestReader
from dify_plugin.core.server.aws.response_writer import AWSResponseWriter


class AWSLambdaRequestReader(RequestReader):
    def __init__(self, port: int, max_single_connection_lifetime: int):
        """
        Initialize the AWSLambdaStream and wait for jobs
        """
        self.app = Flask(__name__)
        self.port = port
        self.max_single_connection_lifetime = max_single_connection_lifetime
        self.request_queue = Queue[PluginInStream]()

        # setup server
        self._serve()

    def _read_stream(self) -> Generator[PluginInStream, None, None]:
        """
        Read request from http server
        """
        while True:
            yield self.request_queue.get()

    def _serve(self):
        """
        Serve the request
        """

        @self.app.route("/invoke", methods=["POST"])
        def server():
            queue = Queue[str]()
            try:
                data = request.get_json()
                event = PluginInStream.Event.value_of(data["event"])
                plugin_in = PluginInStream(
                    event=event,
                    session_id=data["session_id"],
                    data=data["data"],
                    reader=self,
                    writer=AWSResponseWriter(queue),
                )
                # put request to queue
                self.request_queue.put(plugin_in)
                # wait for response
                while True:
                    response = queue.get()
                    if response is None:
                        break
                    yield response
            except Exception as e:
                return str(e)

    def launch(self):
        """
        Launch server
        """
        threading.Thread(
            target=self.app.run, kwargs={"port": self.port, "threaded": True}
        ).start()
