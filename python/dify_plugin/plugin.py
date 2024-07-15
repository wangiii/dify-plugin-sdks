from collections.abc import Generator
import logging
import os
from typing import Type

from pydantic import BaseModel


from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin.setup import (
    PluginConfiguration,
    PluginProviderType,
)
from dify_plugin.core.runtime.entities.plugin.request import (
    ModelInvokeRequest,
    PluginAccessToolRequest,
    PluginInvokeType,
    ToolInvokeRequest,
)
from dify_plugin.core.runtime.session import Session
from dify_plugin.core.server.io_server import IOServer
from dify_plugin.logger_format import plugin_logger_handler
from dify_plugin.model.ai_model import AIModel
from dify_plugin.model.entities import ModelProviderConfiguration
from dify_plugin.model.large_language_model import LargeLanguageModel
from dify_plugin.model.model import ModelProvider
from dify_plugin.model.model_entities import ModelType
from dify_plugin.model.moderation_model import ModerationModel
from dify_plugin.model.rerank_model import RerankModel
from dify_plugin.model.speech2text_model import Speech2TextModel
from dify_plugin.model.text_embedding_model import TextEmbeddingModel
from dify_plugin.model.tts_model import TTSModel
from dify_plugin.tool.entities import (
    ToolConfiguration,
    ToolInvokeMessage,
    ToolProviderConfiguration,
    ToolRuntime,
)
from dify_plugin.tool.tool import Tool, ToolProvider
from dify_plugin.utils.class_loader import (
    load_multi_subclasses_from_source,
    load_single_subclass_from_source,
)
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

    models_configuration: list[ModelProviderConfiguration]
    models_mapping: dict[
        str,
        tuple[
            ModelProviderConfiguration,
            Type[ModelProvider],
            dict[ModelType, Type[AIModel]],
        ],
    ]

    def __init__(self, config: DifyPluginEnv) -> None:
        """
        Initialize plugin
        """
        self.tools_configuration = []
        self.models_configuration = []
        self.tools_mapping = {}
        self.models_mapping = {}

        super().__init__(config)

        # load plugin configuration
        self._load_plugin_configuration()
        # load plugin class
        self._resolve_plugin_cls()

    def _load_plugin_configuration(self):
        """
        load basic plugin configuration from manifest.yaml
        """
        try:
            file = load_yaml_file("manifest.yaml")
            self.configuration = PluginConfiguration(**file)

            for provider in self.configuration.plugins:
                fs = load_yaml_file(provider)
                if fs.get("type") == PluginProviderType.Tool.value:
                    tool_provider_configuration = ToolProviderConfiguration(
                        **fs.get("provider", {})
                    )

                    self.tools_configuration.append(tool_provider_configuration)

                    logger.info(
                        f"Registered tool provider {tool_provider_configuration.identity.name}"
                    )
                elif fs.get("type") == PluginProviderType.Model.value:
                    model_provider_configuration = ModelProviderConfiguration(
                        **fs.get("provider", {})
                    )
                    self.models_configuration.append(model_provider_configuration)

                    logger.info(
                        f"Registered model provider {model_provider_configuration.provider}"
                    )
                else:
                    raise ValueError("Unknown provider type")
        except Exception as e:
            raise ValueError(f"Error loading plugin configuration: {str(e)}")

    def _resolve_tool_providers(self):
        """
        walk through all the tool providers and tools and load the classes from sources
        """
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

    def _resolve_model_providers(self):
        """
        walk through all the model providers and models and load the classes from sources
        """
        for provider in self.models_configuration:
            # load class
            source = provider.extra.python.provider_source
            # remove extension
            module_source = os.path.splitext(source)[0]
            # replace / with .
            module_source = module_source.replace("/", ".")
            cls = load_single_subclass_from_source(
                module_name=module_source,
                script_path=os.path.join(os.getcwd(), source),
                parent_type=ModelProvider,
            )

            # load models class
            models = {}
            for model_source in provider.extra.python.model_sources:
                model_module_source = os.path.splitext(model_source)[0]
                model_module_source = model_module_source.replace("/", ".")
                model_classes = load_multi_subclasses_from_source(
                    module_name=model_module_source,
                    script_path=os.path.join(os.getcwd(), model_source),
                    parent_type=AIModel,
                )

                for model_cls in model_classes:
                    if issubclass(
                        model_cls,
                        (
                            LargeLanguageModel,
                            TextEmbeddingModel,
                            RerankModel,
                            TTSModel,
                            Speech2TextModel,
                            ModerationModel,
                        ),
                    ):
                        models[model_cls.model_type] = model_cls

            self.models_mapping[provider.provider] = (provider, cls, models)

    def _resolve_plugin_cls(self):
        """
        register all plugin extensions
        """
        # load tool providers and tools
        self._resolve_tool_providers()

        # load model providers and models
        self._resolve_model_providers()

    def get_tool_provider_cls(self, provider: str):
        """
        get the tool provider class by provider name
        :param provider: provider name
        :return: tool provider class
        """
        for provider_registration in self.tools_mapping:
            if provider_registration == provider:
                return self.tools_mapping[provider_registration][1]

    def get_tool_cls(self, provider: str, tool: str):
        """
        get the tool class by provider
        :param provider: provider name
        :param tool: tool name
        :return: tool class
        """
        for provider_registration in self.tools_mapping:
            if provider_registration == provider:
                registration = self.tools_mapping[provider_registration][2].get(tool)
                if registration:
                    return registration[1]

    def _execute_request(self, session_id: str, data: dict):
        """
        accept requests and execute
        :param session_id: session id, unique for each request
        :param data: request data
        """
        session = Session(session_id=session_id, executor=self.executer)
        if data.get("type") == PluginInvokeType.Tool.value:
            response = self._execute_tool(session, data)
        elif data.get("type") == PluginInvokeType.Model.value:
            response = self._execute_model(session, data)

        for message in response:
            PluginOutputStream.session_message(
                session_id=session_id,
                data=PluginOutputStream.stream_object(data=message),
            )

    def _execute_tool(
        self, session: Session, data: dict
    ) -> Generator[BaseModel, None, None]:
        """
        accept tool invocation requests and execute
        :param session_id: session id, unique for each request
        :param data: request data
        """
        request = PluginAccessToolRequest(**data)
        if isinstance(request.data, ToolInvokeRequest):
            provider_cls = self.get_tool_provider_cls(request.data.provider)
            if provider_cls is None:
                raise ValueError(f"Provider {request.data.provider} not found")

            tool_cls = self.get_tool_cls(request.data.provider, request.data.tool)
            if tool_cls is None:
                raise ValueError(
                    f"Tool {request.data.tool} not found for provider {request.data.provider}"
                )

            # instantiate provider and tool
            provider = provider_cls()
            tool = tool_cls(
                runtime=ToolRuntime(
                    credentials=request.data.credentials, user_id=request.user_id
                )
            )

            # invoke tool
            return session.run_tool(
                action=request.data.action,
                provider=provider,
                tool=tool,
                parameters=request.data.parameters,
            )
        else:
            raise NotImplementedError("Tool validation not implemented")

    def _execute_model(
        self, session: Session, data: dict
    ) -> Generator[BaseModel, None, None]:
        """
        accept model invocation requests and execute
        :param session_id: session id, unique for each request
        :param data: request data
        """
        request = ModelInvokeRequest(**data)
