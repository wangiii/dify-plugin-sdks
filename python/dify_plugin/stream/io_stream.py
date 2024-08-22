import threading
from typing import Callable, Optional

from pydantic import BaseModel

from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.core.runtime.entities.plugin.message import SessionMessage
from dify_plugin.stream.stream_reader import PluginInputStreamReader, PluginReader
from dify_plugin.stream.stream_writer import (
    PluginOutputStreamWriter,
    Event,
    StreamOutputMessage,
)


class PluginIOStream:
    lock = threading.Lock()
    readers: list[PluginReader] = []
    ready_event = threading.Event()
    stream_reader: Optional[PluginInputStreamReader]
    writer: Optional[PluginOutputStreamWriter]

    def __init__(
        self, writer: PluginOutputStreamWriter, reader: PluginInputStreamReader
    ):
        self.writer = writer
        self.stream_reader = reader
        self.ready_event.set()

    def write(self, data: str):
        if self.writer:
            self.writer.write(data)
        else:
            raise Exception("Output stream writer not initialized")

    def put(
        self,
        event: Event,
        session_id: Optional[str] = None,
        data: Optional[dict | BaseModel] = None,
    ):
        """
        serialize the output to the daemon
        """
        if isinstance(data, BaseModel):
            data = data.model_dump()

        self.write(
            StreamOutputMessage(
                event=event, session_id=session_id, data=data
            ).model_dump_json()
        )
        self.write("\n\n")

    def error(
        self, session_id: Optional[str] = None, data: Optional[dict | BaseModel] = None
    ):
        return self.put(Event.ERROR, session_id, data)

    def log(self, data: Optional[dict] = None):
        return self.put(Event.LOG, None, data)

    def heartbeat(self):
        return self.put(Event.HEARTBEAT, None, {})

    def session_message(
        self, session_id: Optional[str] = None, data: Optional[dict | BaseModel] = None
    ):
        return self.put(Event.SESSION, session_id, data)

    def stream_object(self, data: dict | BaseModel) -> SessionMessage:
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(type=SessionMessage.Type.STREAM, data=data)

    def stream_end_object(self) -> SessionMessage:
        return SessionMessage(type=SessionMessage.Type.END, data={})

    def stream_error_object(self, data: dict | BaseModel) -> SessionMessage:
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(type=SessionMessage.Type.ERROR, data=data)

    def stream_invoke_object(self, data: dict | BaseModel) -> SessionMessage:
        if isinstance(data, BaseModel):
            data = data.model_dump()

        return SessionMessage(type=SessionMessage.Type.INVOKE, data=data)

    def event_loop(self):
        # read line by line
        while True:
            self.ready_event.wait()
            if self.stream_reader is None:
                continue

            for line in self.stream_reader.read():
                if isinstance(line, dict):
                    self._process_line(line)
                else:
                    self._process_line(line[0], hijack=line[1])

    def _process_line(
        self, line: dict, hijack: Optional[Callable[[Callable[[], None]], None]] = None
    ):
        session_id = None
        try:
            data = PluginInStream(**line)
            if hijack:
                data.set_executor_hijack(hijack)

            session_id = data.session_id
            readers: list[PluginReader] = []
            with self.lock:
                for reader in self.readers:
                    if reader.filter(data):
                        readers.append(reader)
            for reader in readers:
                reader.write(data)

        except Exception as e:
            self.error(
                session_id=session_id,
                data={"error": f"Failed to read input: {str(e)}, got: {line}"},
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
