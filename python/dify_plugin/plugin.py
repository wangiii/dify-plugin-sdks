import logging
from typing import Type

from pydantic import BaseModel

from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin import PluginConfiguration
from dify_plugin.core.runtime.entities.request import (
    PluginInvokeType,
    ToolInvokeRequest,
)
from dify_plugin.core.runtime.session import Session
from dify_plugin.core.server.io_server import IOServer
from dify_plugin.logger_format import plugin_logger_handler
from dify_plugin.model.model import Model, ModelProvider
from dify_plugin.tool.entities import ToolRuntime
from dify_plugin.tool.tool import Tool, ToolProvider
from dify_plugin.utils.io_writer import PluginOutputStream
from dify_plugin.utils.yaml_loader import load_yaml_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)

class Plugin(IOServer):
    configuration: PluginConfiguration

    class ToolRegistration(BaseModel):
        cls: Type[ToolProvider]
        tools: list[Type[Tool]]

    tools: list[ToolRegistration]
    models: list[Type[ModelProvider]]

    def __init__(self, config: DifyPluginEnv) -> None:
        self.tools = []
        self.models = []
        super().__init__(config)

        # load plugin configuration
        try:
            file = load_yaml_file('manifest.yaml')
            self.configuration = PluginConfiguration(**file)
        except Exception as e:
            raise ValueError(f"Error loading plugin configuration: {str(e)}")

    def register_model_provider(self, provider: Type[ModelProvider], configuration: str):
        pass

    def register_model(self, tool: Type[Model], configuration: str):
        pass

    def register_tool_provider(self, configuration: str):
        def decorator(tool: Type[ToolProvider]):
            if not issubclass(tool, ToolProvider):
                raise ValueError("Tool must be a subclass of ToolProvider")
            logger.info(f"Registering tool provider {tool.__name__}")
            self.tools.append(self.ToolRegistration(cls=tool, tools=[]))

            return tool

        return decorator

    def register_tool(self, configuration: str):
        def decorator(cls: Type[Tool]):
            if not issubclass(cls, Tool):
                raise ValueError("Tool must be a subclass of Tool")
            logger.info(
                f"Registering tool {cls.__name__} for provider {configuration}"
            )
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

    async def _execute_request(self, session_id: str, data: dict):
        session = Session(session_id=session_id, executor=self.executer)
        if data.get("type") == PluginInvokeType.Tool.value:
            request = ToolInvokeRequest(**data)

            provider_cls = self.get_tool_provider_cls(request.provider)
            if provider_cls is None:
                raise ValueError(f"Provider {request.provider} not found")

            tool_cls = self.get_tool_cls(provider_cls, request.tool)
            if tool_cls is None:
                raise ValueError(
                    f"Tool {request.tool} not found for provider {request.provider}"
                )

            provider = provider_cls()
            tool = tool_cls(
                runtime=ToolRuntime(
                    credentials=request.credentials, user_id=request.user_id
                )
            )

            response = session.run_tool(
                action=request.action,
                provider=provider,
                tool=tool,
                parameters=request.parameters,
            )

            async for message in response:
                PluginOutputStream.session_message(
                    session_id=session_id,
                    data=PluginOutputStream.stream_object(data=message),
                )

        elif data.get("type") == PluginInvokeType.Model.value:
            request = ToolInvokeRequest(**data)
