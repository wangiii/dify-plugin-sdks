import logging
import sys
from typing import Type

from pydantic import BaseModel

from dify_plugin.core.server.io_server import IOServer
from dify_plugin.logger_format import DifyPluginLoggerFormatter
from dify_plugin.model.model import Model, ModelProvider
from dify_plugin.tool.tool import Tool, ToolProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(DifyPluginLoggerFormatter())

logger.addHandler(handler)

class Plugin(IOServer):
    class ToolRegistration(BaseModel):
        cls: Type[ToolProvider]
        tools: list[Type[Tool]]

    tools: list[ToolRegistration]
    models: list[Type[ModelProvider]]

    def __init__(self) -> None:
        self.tools = []
        self.models = []

        super().__init__()

    def register_model_provider(self, provider: Type[ModelProvider]):
        pass

    def register_model(self, tool: Type[Model]):
        pass

    def register_tool_provider(self, tool: Type[ToolProvider]):
        if not issubclass(tool, ToolProvider):
            raise ValueError('Tool must be a subclass of ToolProvider')
        logger.info(f'Registering tool provider {tool.__name__}')
        self.tools.append(self.ToolRegistration(cls=tool, tools=[]))

        return tool

    def register_tool(self, provider: Type[ToolProvider]):
        def decorator(cls: Type[Tool]):
            if not issubclass(cls, Tool):
                raise ValueError('Tool must be a subclass of Tool')
            logger.info(f'Registering tool {cls.__name__} for provider {provider.__name__}')
            for tool_registration in self.tools:
                if tool_registration.cls == provider:
                    tool_registration.tools.append(cls)
                    break
            else:
                raise ValueError(f'Provider {provider.__name__} not found')
            
            return cls
        
        return decorator
    
    def get_tool_provider_cls(self, provider: str):
        for provider_registration in self.tools:
            if provider_registration.cls.configuration().name == provider:
                return provider_registration.cls
        return None
    
    def get_tool_cls(self, provider: Type[ToolProvider], tool: str):
        for tool_registration in self.tools:
            if tool_registration.cls == provider:
                for tool_cls in tool_registration.tools:
                    if tool_cls.configuration().name == tool:
                        return tool_cls
        return None

    async def _execute_request(self, data: dict):
        print(data)

    