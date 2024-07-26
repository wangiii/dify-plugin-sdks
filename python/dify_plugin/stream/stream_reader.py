from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from queue import Queue
import queue
from typing import Optional, overload


from dify_plugin.core.runtime.entities.plugin.io import PluginInStream


class PluginReader:
    filter: Callable[[PluginInStream], bool]
    queue: Queue[PluginInStream | None]
    close_callback: Optional[Callable]

    def __init__(
        self,
        filter: Callable[[PluginInStream], bool],
        close_callback: Optional[Callable] = None,
    ) -> None:
        self.filter = filter
        self.queue = Queue()
        self.close_callback = close_callback

    @overload
    def read(
        self, timeout_for_round: float
    ) -> Generator[PluginInStream | None, None, None]: ...

    @overload
    def read(self) -> Generator[PluginInStream, None, None]: ...

    def read(
        self, timeout_for_round: Optional[float] = None
    ) -> Generator[PluginInStream | None, None, None]:
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


class PluginInputStreamReader(ABC):
    @abstractmethod
    def read(self) -> Generator[dict, None, None]:
        """
        read data from the stream infinitely
        """
