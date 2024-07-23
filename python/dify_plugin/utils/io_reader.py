from collections.abc import Callable, Generator
from queue import Queue
import queue
import sys
import threading
from typing import Optional, overload

from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
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

    @overload
    def read(self, timeout_for_round: float) -> Generator[PluginInStream | None, None, None]:
        ...

    @overload
    def read(self) -> Generator[PluginInStream, None, None]:
        ...

    def read(self, timeout_for_round: Optional[float] = None) -> Generator[PluginInStream | None, None, None]:
        while True:
            try:
                data = self.queue.get(timeout=timeout_for_round)
            except queue.Empty:
                yield None
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

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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
                PluginOutputStream.error(session_id=session_id, data={'error': f'Failed to read input: {str(e)}, got: {line}'})

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
