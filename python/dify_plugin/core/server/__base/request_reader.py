import threading
from typing import Callable, Optional


from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.core.server.__base.stream_reader import (
    PluginInputStreamReader,
    PluginReader,
)

class RequestReader:
    lock = threading.Lock()
    readers: list[PluginReader] = []
    stream_reader: Optional[PluginInputStreamReader]

    def __init__(self, reader: PluginInputStreamReader):
        self.stream_reader = reader

    def event_loop(self):
        # read line by line
        while True:
            if self.stream_reader is None:
                continue

            for line in self.stream_reader.read():
                self._process_line(line)

    def _process_line(self, data: PluginInStream):
        try:
            session_id = data.session_id
            readers: list[PluginReader] = []
            with self.lock:
                for reader in self.readers:
                    if reader.filter(data):
                        readers.append(reader)
            for reader in readers:
                reader.write(data)
        except Exception as e:
            data.writer.error(
                session_id=session_id,
                data={
                    "error": f"Failed to process request ({type(e).__name__}): {str(e)}"
                },
            )

    def read(self, filter: Callable[[PluginInStream], bool]) -> PluginReader:
        def close(reader: PluginReader):
            with self.lock:
                self.readers.remove(reader)

        reader = PluginReader(filter, close_callback=lambda: close(reader))

        with self.lock:
            self.readers.append(reader)

        return reader

    def close(self):
        """
        close stdin processing
        """
        for reader in self.readers:
            reader.close()
        self.readers.clear()
