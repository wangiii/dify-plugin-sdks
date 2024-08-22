from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import time
from typing import Callable, Optional
from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.stream.io_stream import PluginIOStream


class IOServer(ABC):
    io_stream: PluginIOStream

    def __init__(self, config: DifyPluginEnv, io_stream: PluginIOStream) -> None:
        self.config = config
        self.executer = ThreadPoolExecutor(max_workers=self.config.MAX_WORKER)
        self.io_stream = io_stream

    def close(self, *args):
        self.io_stream.close()

    @abstractmethod
    def _execute_request(self, session_id: str, data: dict):
        """
        accept requests and execute them, should be implemented outside
        """

    def _setup_instruction_listener(self):
        """
        start listen to stdin and dispatch task to executor
        """

        def filter(data: PluginInStream) -> bool:
            if data.event == PluginInStream.Event.Request:
                return True
            return False

        for data in self.io_stream.read(filter).read():
            self.executer.submit(
                self._hijack_execute_request,
                data.session_id,
                data.data,
                data.get_executor_hijack(),
            )

    def _hijack_execute_request(
        self,
        session_id: str,
        data: dict,
        hijack: Optional[Callable[[Callable[[], None]], None]],
    ):
        """
        hijack the executor
        """
        if hijack:
            hijack(lambda: self._execute_request_thread(session_id, data))
        else:
            self._execute_request_thread(session_id, data)

    def _execute_request_thread(
        self,
        session_id: str,
        data: dict,
    ):
        """
        wrapper for _execute_request
        """
        # wait for the task to finish
        try:
            self._execute_request(session_id, data)
        except Exception as e:
            self.io_stream.session_message(
                session_id=session_id,
                data=self.io_stream.stream_error_object(
                    data={
                        "error": f"Failed to execute request ({type(e).__name__}): {str(e)}"
                    }
                ),
            )

        self.io_stream.session_message(
            session_id=session_id, data=self.io_stream.stream_end_object()
        )

    def _heartbeat(self):
        """
        send heartbeat to stdout
        """
        while True:
            # timer
            try:
                self.io_stream.heartbeat()
            except Exception:
                pass
            time.sleep(self.config.HEARTBEAT_INTERVAL)

    def _run(self):
        th1 = Thread(target=self._setup_instruction_listener)
        th2 = Thread(target=self.io_stream.event_loop)
        th3 = Thread(target=self._heartbeat)

        th1.start()
        th2.start()
        th3.start()

        th1.join()
        th2.join()
        th3.join()

    def run(self):
        """
        start plugin server
        """
        self._run()
