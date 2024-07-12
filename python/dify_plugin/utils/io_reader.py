import asyncio
from collections.abc import AsyncGenerator, Callable
import sys
from typing import Any, Coroutine, Optional

from dify_plugin.core.runtime.entities.io import PluginInStream
from dify_plugin.utils.io_writer import PluginOutputStream

class PluginReader:
    filter: Callable[[PluginInStream], bool]
    queue: asyncio.Queue[PluginInStream | None]
    close_callback: Optional[Callable[[], Coroutine[Any, Any, None]]]

    def __init__(self, filter: Callable[[PluginInStream], bool],
                    close_callback: Optional[Callable[[], Coroutine[Any, Any, None]]] = None) -> None:
        self.filter = filter
        self.queue = asyncio.Queue()
        self.close_callback = close_callback

    async def read(self) -> AsyncGenerator[PluginInStream]:
        """
        read data asynchronously from plugin
        """
        while True:
            try:
                data = await self.queue.get()
            except asyncio.CancelledError:
                break

            if data is None:
                break
            yield data

    async def close(self):
        if self.close_callback:
            await self.close_callback()

        await self.queue.put(None)

    async def write(self, data: PluginInStream):
        await self.queue.put(data)

class PluginInputStream:
    lock = asyncio.Lock()
    readers: list[PluginReader] = []

    @classmethod
    async def event_loop(cls):
        loop = asyncio.get_event_loop()
        stdin_reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(stdin_reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await stdin_reader.readline()
            except asyncio.CancelledError:
                break
            
            session_id = None
            try:
                data = PluginInStream.model_validate_json(line)
                session_id = data.session_id
                readers: list[PluginReader] = []
                async with cls.lock:
                    for reader in cls.readers:
                        if reader.filter(data):
                            readers.append(reader)
                for reader in readers:
                    await reader.write(data)
            except Exception as e:
                PluginOutputStream.error(session_id=session_id, data={'error': str(e)})

    @classmethod
    async def read(cls, filter: Callable[[PluginInStream], bool]) -> PluginReader:
        async def close(reader: PluginReader):
            async with cls.lock:
                cls.readers.remove(reader)

        reader = PluginReader(filter, close_callback=lambda : close(reader))
        
        async with cls.lock:
            cls.readers.append(reader)

        return reader