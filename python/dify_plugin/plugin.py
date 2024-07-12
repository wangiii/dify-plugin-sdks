import logging
import os
from typing import Any, Type


from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin import (
    PluginConfiguration,
    PluginProviderType,
)
from dify_plugin.core.runtime.entities.request import (
    PluginInvokeType,
    ToolInvokeRequest,
)
from dify_plugin.core.runtime.session import Session
from dify_plugin.core.server.io_server import IOServer
from dify_plugin.logger_format import plugin_logger_handler
from dify_plugin.tool.entities import (
    ToolConfiguration,
    ToolProviderConfiguration,
    ToolRuntime,
)
from dify_plugin.tool.tool import Tool, ToolProvider
from dify_plugin.utils.class_loader import load_single_subclass_from_source
from dify_plugin.utils.io_writer import PluginOutputStream
from dify_plugin.utils.yaml_loader import load_yaml_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class Plugin(IOServer):
    configuration: PluginConfiguration
    tools_configuration: list[ToolProviderConfiguration]
    tools_mapping: dict[
        str,
        tuple[
            ToolProviderConfiguration,
            Type[ToolProvider],
            dict[str, tuple[ToolConfiguration, Type[Tool]]],
        ],
    ]

    def __init__(self, config: DifyPluginEnv) -> None:
        self.tools_configuration = []
        self.tools_mapping = {}

        super().__init__(config)

        # load plugin configuration
        self._load_plugin_configuration()
        # load plugin class
        self._load_plugin_cls()

    def _load_plugin_configuration(self):
        try:
            file = load_yaml_file("manifest.yaml")
            self.configuration = PluginConfiguration(**file)

            for provider in self.configuration.plugins:
                fs = load_yaml_file(provider)
                if fs.get("type") == PluginProviderType.Tool.value:
                    credentials_for_provider: dict[str, Any] = fs.get(
                        "provider", {}
                    ).get("credentials_for_provider", {})
                    self._fill_in_credentials(credentials_for_provider)

                    tool_provider_configuration = ToolProviderConfiguration(
                        **fs.get("provider", {})
                    )
                    self.tools_configuration.append(tool_provider_configuration)

                    logger.info(
                        f"Registered tool provider {tool_provider_configuration.identity.name}"
                    )
        except Exception as e:
            raise ValueError(f"Error loading plugin configuration: {str(e)}")

    def _fill_in_credentials(self, credentials_for_provider: dict[str, Any]):
        for credential in credentials_for_provider:
            credentials_for_provider[credential]["name"] = credential
        return credentials_for_provider

    def _load_plugin_cls(self):
        for provider in self.tools_configuration:
            # load class
            source = provider.extra.python.source
            # remove extension
            module_source = os.path.splitext(source)[0]
            # replace / with .
            module_source = module_source.replace("/", ".")
            cls = load_single_subclass_from_source(
                module_name=module_source,
                script_path=os.path.join(os.getcwd(), source),
                parent_type=ToolProvider,
            )

            # load tools class
            tools = {}
            for tool in provider.tools:
                tool_source = tool.extra.python.source
                tool_module_source = os.path.splitext(tool_source)[0]
                tool_module_source = tool_module_source.replace("/", ".")
                tool_cls = load_single_subclass_from_source(
                    module_name=tool_module_source,
                    script_path=os.path.join(os.getcwd(), tool_source),
                    parent_type=Tool,
                )

                tools[tool.identity.name] = (tool, tool_cls)

            self.tools_mapping[provider.identity.name] = (provider, cls, tools)

    def get_tool_provider_cls(self, provider: str):
        for provider_registration in self.tools_mapping:
            if provider_registration == provider:
                return self.tools_mapping[provider_registration][1]

    def get_tool_cls(self, provider: str, tool: str):
        for provider_registration in self.tools_mapping:
            if provider_registration == provider:
                registration = self.tools_mapping[provider_registration][2].get(tool)
                if registration:
                    return registration[1]

    async def _execute_request(self, session_id: str, data: dict):
        session = Session(session_id=session_id, executor=self.executer)
        if data.get("type") == PluginInvokeType.Tool.value:
            request = ToolInvokeRequest(**data)
            provider_cls = self.get_tool_provider_cls(request.provider)
            if provider_cls is None:
                raise ValueError(f"Provider {request.provider} not found")

            tool_cls = self.get_tool_cls(request.provider, request.tool)
            if tool_cls is None:
                raise ValueError(
                    f"Tool {request.tool} not found for provider {request.provider}"
                )

            provider = provider_cls()
            tool = tool_cls(
                runtime=ToolRuntime(
                    credentials=request.credentials,
                    user_id=request.user_id
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
