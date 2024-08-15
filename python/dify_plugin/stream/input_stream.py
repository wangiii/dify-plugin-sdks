import threading
from typing import Callable, Optional

from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.stream.output_stream import PluginOutputStream
from dify_plugin.stream.stream_reader import PluginInputStreamReader, PluginReader


class PluginInputStream:
    lock = threading.Lock()
    readers: list[PluginReader] = []
    ready_event = threading.Event()
    stream_reader: Optional[PluginInputStreamReader] = None

    @classmethod
    def reset(cls, reader: PluginInputStreamReader):
        cls.stream_reader = reader
        cls.ready_event.set()

    @classmethod
    def event_loop(cls):
        # read line by line
        while True:
            cls.ready_event.wait()
            if cls.stream_reader is None:
                continue

            for line in cls.stream_reader.read():
                if isinstance(line, dict):
                    cls._process_line(line)
                else:
                    cls._process_line(line[0], hijack=line[1])

    @classmethod
    def _process_line(cls, line: dict, hijack: Optional[Callable[[Callable[[], None]], None]] = None):
        session_id = None
        try:
            data = PluginInStream(**line)
            if hijack:
                data.set_executor_hijack(hijack)
                
            session_id = data.session_id
            readers: list[PluginReader] = []
            with cls.lock:
                for reader in cls.readers:
                    if reader.filter(data):
                        readers.append(reader)
            for reader in readers:
                reader.write(data)

        except Exception as e:
            PluginOutputStream.error(
                session_id=session_id,
                data={"error": f"Failed to read input: {str(e)}, got: {line}"},
            )

    @classmethod
    def read(cls, filter: Callable[[PluginInStream], bool]) -> PluginReader:
        def close(reader: PluginReader):
            with cls.lock:
                cls.readers.remove(reader)

        reader = PluginReader(filter, close_callback=lambda: close(reader))

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
