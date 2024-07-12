from collections.abc import Callable, Generator
from queue import Queue
import signal
import sys
import threading
from typing import Optional

from dify_plugin.core.runtime.entities.io import PluginInStream
from dify_plugin.utils.io_writer import PluginOutputStream

class PluginReader:
    filter: Callable[[PluginInStream], bool]
    queue: Queue[PluginInStream | None]
    close_callback: Optional[Callable]

    def __init__(self, filter: Callable[[PluginInStream], bool],
                    close_callback: Optional[Callable] = None) -> None:
        self.filter = filter
        self.queue = Queue()
        self.close_callback = close_callback

    def read(self) -> Generator[PluginInStream, None, None]:
        while True:
            try:
                data = self.queue.get()
            except Exception:
                break

            if data is None:
                break

            yield data

    def close(self):
        if self.close_callback:
            self.close_callback()

        self.queue.put(None)

    def write(self, data: PluginInStream):
        self.queue.put(data)

class PluginInputStream:
    lock = threading.Lock()
    readers: list[PluginReader] = []

    @classmethod
    def event_loop(cls):
        # read line by line
        for line in sys.stdin:
            session_id = None
            try:
                data = PluginInStream.model_validate_json(line)
                session_id = data.session_id
                readers: list[PluginReader] = []
                with cls.lock:
                    for reader in cls.readers:
                        if reader.filter(data):
                            readers.append(reader)
                for reader in readers:
                    reader.write(data)
            except Exception as e:
                PluginOutputStream.error(session_id=session_id, data={'error': str(e)})

        cls.close()
        
    @classmethod
    def read(cls, filter: Callable[[PluginInStream], bool]) -> PluginReader:
        def close(reader: PluginReader):
            with cls.lock:
                cls.readers.remove(reader)

        reader = PluginReader(filter, close_callback=lambda : close(reader))
        
        with cls.lock:
            cls.readers.append(reader)

        return reader
    
    @classmethod
    def close(cls):
        """
        close stdin processing
        """
        for reader in cls.readers:
            reader.close()
        cls.readers.clear()
