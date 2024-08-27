from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import time
from typing import Optional
from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin.io import (
    PluginInStream,
    PluginInStreamEvent,
)
from dify_plugin.core.server.__base.request_reader import RequestReader
from dify_plugin.core.server.__base.response_writer import ResponseWriter


class IOServer(ABC):
    io_stream: RequestReader

    def __init__(
        self,
        config: DifyPluginEnv,
        io_stream: RequestReader,
        default_writer: Optional[ResponseWriter],
    ) -> None:
        self.config = config
        self.default_writer = default_writer
        self.executer = ThreadPoolExecutor(max_workers=self.config.MAX_WORKER)
        self.io_stream = io_stream

    def close(self, *args):
        self.io_stream.close()

    @abstractmethod
    def _execute_request(
        self, session_id: str, data: dict, reader: RequestReader, writer: ResponseWriter
    ):
        """
        accept requests and execute them, should be implemented outside
        """

    def _setup_instruction_listener(self):
        """
        start listen to stdin and dispatch task to executor
        """

        def filter(data: PluginInStream) -> bool:
            if data.event == PluginInStreamEvent.Request:
                return True
            return False

        for data in self.io_stream.read(filter).read():
            self.executer.submit(
                self._execute_request_thread,
                data.session_id,
                data.data,
                data.reader,
                data.writer,
            )

    def _execute_request_thread(
        self, session_id: str, data: dict, reader: RequestReader, writer: ResponseWriter
    ):
        """
        wrapper for _execute_request
        """
        # wait for the task to finish
        try:
            self._execute_request(session_id, data, reader, writer)
        except Exception as e:
            writer.session_message(
                session_id=session_id,
                data=writer.stream_error_object(
                    data={
                        "error": f"Failed to execute request ({type(e).__name__}): {str(e)}"
                    }
                ),
            )

        writer.session_message(session_id=session_id, data=writer.stream_end_object())

    def _heartbeat(self):
        """
        send heartbeat to stdout
        """
        assert self.default_writer

        while True:
            # timer
            try:
                self.default_writer.heartbeat()
            except Exception:
                pass
            time.sleep(self.config.HEARTBEAT_INTERVAL)

    def _run(self):
        th1 = Thread(target=self._setup_instruction_listener)
        th2 = Thread(target=self.io_stream.event_loop)

        if self.default_writer:
            th3 = Thread(target=self._heartbeat)

        th1.start()
        th2.start()

        if self.default_writer:
            th3.start()

        th1.join()
        th2.join()

        if self.default_writer:
            th3.join()

    def run(self):
        """
        start plugin server
        """
        self._run()
