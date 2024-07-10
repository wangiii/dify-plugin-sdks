from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from dify_plugin.core.runtime.entities.tool import ToolInvokeMessage, ToolInvokeTextMessage
from dify_plugin.core.runtime.request import RequestInterface
from dify_plugin.tool.entities import ToolConfiguration, ToolProviderConfiguration, ToolRuntime


class ToolProvider(ABC):
    @classmethod
    @abstractmethod
    def configuration(cls) -> ToolProviderConfiguration:
        return

class Tool(RequestInterface, ABC):
    runtime: ToolRuntime

    def __init__(self, runtime: ToolRuntime):
        self.runtime = runtime

    @classmethod
    @abstractmethod
    def configuration(cls) -> ToolConfiguration:
        return

    def create_text_message(self, text: str) -> ToolInvokeTextMessage:
        return ToolInvokeTextMessage(message=ToolInvokeMessage.TextMessage(text=text))

    @abstractmethod
    async def _invoke(self, user_id: str, tool_parameter: dict) -> AsyncGenerator[ToolInvokeMessage, None]:
        pass