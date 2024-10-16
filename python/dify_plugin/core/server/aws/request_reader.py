from queue import Queue
import threading
from typing import Generator
from flask import Flask, request
from ....core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamEvent,
)
from ....core.server.__base.request_reader import RequestReader
from .response_writer import AWSResponseWriter


class AWSLambdaRequestReader(RequestReader):
    def __init__(self, port: int, max_single_connection_lifetime: int):
        """
        Initialize the AWSLambdaStream and wait for jobs
        """
        self.app = Flask(__name__)
        self.port = port
        self.max_single_connection_lifetime = max_single_connection_lifetime
        self.request_queue = Queue[PluginInStream]()

    def _read_stream(self) -> Generator[PluginInStream, None, None]:
        """
        Read request from http server
        """
        while True:
            yield self.request_queue.get()

    def handler(self):
        try:
            queue = Queue[str]()
            data = request.get_json()
            event = PluginInStreamEvent.value_of(data["event"])
            plugin_in = PluginInStream(
                event=event,
                session_id=data["session_id"],
                conversation_id=data.get("conversation_id"),
                message_id=data.get("message_id"),
                app_id=data.get("app_id"),
                endpoint_id=data.get("endpoint_id"),
                data=data["data"],
                reader=self,
                writer=AWSResponseWriter(queue),
            )
            # put request to queue
            self.request_queue.put(plugin_in)
            # wait for response
            def generate():
                while True:
                    response = queue.get()
                    if response is None:
                        break
                    yield response
            return generate(), 200
        except Exception as e:
            return str(e), 500

    def _run(self):
        self.app.route("/invoke", methods=["POST"])(self.handler)
        self.app.run(port=self.port, threaded=True, debug=False)

    def launch(self):
        """
        Launch server
        """
        threading.Thread(target=self._run).start()
