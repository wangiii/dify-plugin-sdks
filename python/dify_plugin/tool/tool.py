from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Optional

from dify_plugin.core.runtime.request import RequestInterface
from dify_plugin.core.runtime.session import Session
from dify_plugin.tool.entities import ToolInvokeMessage, ToolRuntime


class ToolProvider(ABC):
    def validate_credentials(self, credentials: dict):
        return self._validate_credentials(credentials)

    @abstractmethod
    def _validate_credentials(self, credentials: dict):
        pass


class Tool(RequestInterface, ABC):
    runtime: ToolRuntime

    def __init__(
        self,
        runtime: ToolRuntime,
        session: Optional[Session] = None,
    ):
        self.runtime = runtime
        RequestInterface.__init__(self, session)

    @classmethod
    def from_credentials(
        cls,
        credentials: dict,
    ) -> "Tool":
        return cls(
            ToolRuntime(credentials=credentials, user_id=None, session_id=None),
        )

    def create_text_message(self, text: str) -> ToolInvokeMessage:
        return ToolInvokeMessage(
            type=ToolInvokeMessage.MessageType.TEXT,
            message=ToolInvokeMessage.TextMessage(text=text),
        )

    def create_json_message(self, json: dict) -> ToolInvokeMessage:
        return ToolInvokeMessage(
            type=ToolInvokeMessage.MessageType.JSON,
            message=ToolInvokeMessage.JsonMessage(json_object=json),
        )

    @abstractmethod
    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None]:
        pass

    def invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None]:
        return self._invoke(tool_parameters)
