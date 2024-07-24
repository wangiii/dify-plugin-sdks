from collections.abc import Generator
import os
import sys

from gevent.select import select

from dify_plugin.stream.stream_reader import PluginInputStreamReader
from dify_plugin.stream.stream_writer import PluginOutputStreamWriter


class StdioStream(PluginOutputStreamWriter, PluginInputStreamReader):
    def write(self, data: str):
        sys.stdout.write(data)
        sys.stdout.flush()

    def read(self) -> Generator[str, None, None]:
        buffer = ""
        while True:
            ready, _, _ = select([sys.stdin], [], [], 1)
            if not ready:
                continue

            # read data from stdin through os.read to avoid buffering related issues
            data = os.read(sys.stdin.fileno(), 4096).decode()

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
                yield line
