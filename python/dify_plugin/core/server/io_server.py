from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.utils.io_reader import PluginInputStream
from dify_plugin.utils.io_writer import PluginOutputStream

class IOServer(ABC):
    def __init__(self, config: DifyPluginEnv) -> None:
        self.config = config
        self.executer = ThreadPoolExecutor(max_workers=self.config.MAX_WORKER)

    def close(self, *args):
        PluginInputStream.close()

    @abstractmethod
    def _execute_request(self, session_id: str, data: dict):
        pass

    def _setup_instruction_listener(self):
        def filter(data: PluginInStream) -> bool:
            if data.event == PluginInStream.Event.Request:
                return True
            return False
        
        for data in PluginInputStream.read(filter).read():
            self.executer.submit(self._execute_request_thread, data.session_id, data.data)

    def _execute_request_thread(self, session_id: str, data: dict):
        # wait for the task to finish
        try:
            self._execute_request(session_id, data)
        except Exception as e:
            PluginOutputStream.error(session_id=session_id, data={'error': str(e)})

        PluginOutputStream.log(data={'message': 'Task finished', 'session_id': session_id})

    def _run(self):
        th1 = Thread(target=self._setup_instruction_listener)
        th2 = Thread(target=PluginInputStream.event_loop)

        th1.start()
        th2.start()

        th1.join()
        th2.join()

    def run(self):
        self._run()
