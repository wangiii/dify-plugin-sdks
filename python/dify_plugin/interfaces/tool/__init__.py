from abc import ABC, abstractmethod
from collections.abc import Generator

from dify_plugin.entities.tool import ToolInvokeMessage, ToolRuntime
from dify_plugin.core.runtime import Session


class ToolProvider(ABC):
    def validate_credentials(self, credentials: dict):
        return self._validate_credentials(credentials)

    @abstractmethod
    def _validate_credentials(self, credentials: dict):
        pass


class Tool(ABC):
    runtime: ToolRuntime

    def __init__(
        self,
        runtime: ToolRuntime,
        session: Session,
    ):
        self.runtime = runtime
        self.session = session

    @classmethod
    def from_credentials(
        cls,
        credentials: dict,
    ) -> "Tool":
        return cls(
            runtime=ToolRuntime(credentials=credentials, user_id=None, session_id=None),
            session=Session.empty_session(),  # TODO could not fetch session here
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
