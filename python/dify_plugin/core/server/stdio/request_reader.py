from json import loads
import sys
from typing import Generator
from ....core.entities.plugin.io import (
    PluginInStream,
    PluginInStreamEvent,
)

from gevent.os import tp_read

from ....core.server.__base.request_reader import RequestReader
from .response_writer import StdioResponseWriter


class StdioRequestReader(RequestReader):
    def _read_stream(self) -> Generator[PluginInStream, None, None]:
        buffer = b""
        while True:
            # read data from stdin through tp_read
            data = tp_read(sys.stdin.fileno(), 512)

            if not data:
                continue

            buffer += data

            # process line by line and keep the last line if it is not complete
            lines = buffer.split(b"\n")
            if len(lines) == 0:
                continue

            if lines[-1] != b"":
                buffer = lines[-1]
            else:
                buffer = b""

            lines = lines[:-1]
            for line in lines:
                try:
                    data = loads(line)
                    yield PluginInStream(
                        session_id=data["session_id"],
                        event=PluginInStreamEvent.value_of(data["event"]),
                        data=data["data"],
                        reader=self,
                        writer=StdioResponseWriter(),
                    )
                except Exception as e:
                    StdioResponseWriter().error(data={"error": str(e)})
