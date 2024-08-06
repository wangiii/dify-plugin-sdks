from collections.abc import Generator
from json import loads
import sys

# import tp_read
from gevent.os import tp_read

from dify_plugin.stream.stream_reader import PluginInputStreamReader
from dify_plugin.stream.stream_writer import PluginOutputStreamWriter


class StdioStream(PluginOutputStreamWriter, PluginInputStreamReader):
    def write(self, data: str):
        sys.stdout.write(data)
        sys.stdout.flush()

    def read(self) -> Generator[dict, None, None]:
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
                    yield loads(line)
                except Exception:
                    pass
