from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import time
from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.stream.input_stream import PluginInputStream
from dify_plugin.stream.output_stream import PluginOutputStream


class IOServer(ABC):
    def __init__(self, config: DifyPluginEnv) -> None:
        self.config = config
        self.executer = ThreadPoolExecutor(max_workers=self.config.MAX_WORKER)

    def close(self, *args):
        PluginInputStream.close()

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

        for data in PluginInputStream.read(filter).read():
            self.executer.submit(
                self._execute_request_thread, data.session_id, data.data
            )

    def _execute_request_thread(self, session_id: str, data: dict):
        """
        wrapper for _execute_request
        """
        # wait for the task to finish
        try:
            self._execute_request(session_id, data)
        except Exception as e:
            PluginOutputStream.session_message(
                session_id=session_id,
                data=PluginOutputStream.stream_error_object(
                    data={
                        "error": f"Failed to execute request ({type(e).__name__}): {str(e)}"
                    }
                ),
            )

        PluginOutputStream.session_message(
            session_id=session_id, data=PluginOutputStream.stream_end_object()
        )

    def _heartbeat(self):
        """
        send heartbeat to stdout
        """
        while True:
            # timer
            PluginOutputStream.heartbeat()
            time.sleep(self.config.HEARTBEAT_INTERVAL)

    def _run(self):
        th1 = Thread(target=self._setup_instruction_listener)
        th2 = Thread(target=PluginInputStream.event_loop)
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
