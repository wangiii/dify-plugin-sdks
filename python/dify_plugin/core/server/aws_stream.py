from collections.abc import Generator
from dify_plugin.stream.stream_reader import PluginInputStreamReader
from dify_plugin.stream.stream_writer import PluginOutputStreamWriter


class AWSLambdaStream(PluginOutputStreamWriter, PluginInputStreamReader):
    def __init__(self):
        """
        Initialize the AWSLambdaStream and wait for jobs
        """

    def write(self, data: str):
        """
        Write data to http response
        """
        return super().write(data)
    
    def read(self) -> Generator[dict, None, None]:
        """
        Read data from http request
        """
        return super().read()
    
    def launch(self):
        """
        Launch server
        """