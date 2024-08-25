from json import loads
import sys
from typing import Generator
from dify_plugin.core.runtime.entities.plugin.io import PluginInStream
from dify_plugin.core.server.__base.stream_reader import PluginInputStreamReader

from gevent.os import tp_read

from dify_plugin.core.server.stdio.response_writer import StdioResponseWriter


class StdioRequestReader(PluginInputStreamReader):
    def read(self) -> Generator[PluginInStream, None, None]:
        buffer = ""
        while True:
            # read data from stdin through tp_read
            data = tp_read(sys.stdin.fileno(), 512).decode()

            if not data:
                continue
            buffer += data

            # process line by line and keep the last line if it is not complete
            lines = buffer.split("\n")
            if len(lines) == 0:
                continue

            if lines[-1] != "":
                buffer = lines[-1]
            else:
                buffer = ""

            lines = lines[:-1]
            for line in lines:
                try:
                    data = loads(line)
                    yield PluginInStream(
                        session_id=data["session_id"],
                        event=PluginInStream.Event.value_of(data["event"]),
                        data=data["data"],
                        writer=StdioResponseWriter(),
                    )
                except Exception as e:
                    StdioResponseWriter().error(data={"error": str(e)})
