from collections.abc import Generator
from typing import Any

from pydantic import BaseModel
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest

from enum import Enum


class ToolProviderType(Enum):
    """
        Enum class for tool provider
    """
    BUILT_IN = "builtin"
    WORKFLOW = "workflow"
    API = "api"
    APP = "app"
    DATASET_RETRIEVAL = "dataset-retrieval"

    @classmethod
    def value_of(cls, value: str) -> 'ToolProviderType':
        """
        Get value of given mode.

        :param value: mode value
        :return: mode
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f'invalid mode value {value}')
    

class ToolInvokeMessage(BaseModel):
    class TextMessage(BaseModel):
        text: str

        def to_dict(self):
            return {"text": self.text}

    class JsonMessage(BaseModel):
        json_object: dict

        def to_dict(self):
            return {"json_object": self.json_object}

    class MessageType(Enum):
        TEXT = "text"
        FILE = "file"
        BLOB = "blob"
        JSON = "json"

    type: MessageType
    message: TextMessage | JsonMessage

    def to_dict(self):
        return {"type": self.type.value, "message": self.message.to_dict()}
    

class ToolRequest(DifyRequest[ToolInvokeMessage]):
    def invoke_builtin_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke builtin tool
        """
        return self.invoke(
            ToolProviderType.BUILT_IN, provider, tool_name, parameters
        )

    def invoke_workflow_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke workflow tool
        """
        return self.invoke(
            ToolProviderType.WORKFLOW, provider, tool_name, parameters
        )

    def invoke_api_tool(
        self, provider: str, tool_name: str, parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke api tool
        """
        return self.invoke(ToolProviderType.API, provider, tool_name, parameters)

    def invoke(
        self,
        provider_type: ToolProviderType,
        provider: str,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke tool
        """
        return self._backwards_invoke(
            InvokeType.Tool,
            ToolInvokeMessage,
            {
                "provider_type": provider_type.value,
                "provider": provider,
                "tool": tool_name,
                "tool_parameters": parameters,
            },
        )
