import logging
import os
from typing import Type
from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.core.runtime.entities.plugin.setup import (
    PluginConfiguration,
    PluginProviderType,
)
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
from dify_plugin.tool.entities import ToolConfiguration, ToolProviderConfiguration
from dify_plugin.tool.tool import Tool, ToolProvider
from dify_plugin.utils.class_loader import (
    load_multi_subclasses_from_source,
    load_single_subclass_from_source,
)
from dify_plugin.utils.yaml_loader import load_yaml_file
from dify_plugin.logger_format import plugin_logger_handler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class PluginRegistration:
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
            ModelProvider,
            dict[ModelType, AIModel],
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
                elif fs.get("type") == PluginProviderType.Model.value:
                    model_provider_configuration = ModelProviderConfiguration(
                        **fs.get("provider", {})
                    )
                    self.models_configuration.append(model_provider_configuration)
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

    def _is_strict_subclass(self, cls: Type, *parent_cls: Type) -> bool:
        """
        check if the class is a strict subclass of one of the parent classes
        """
        for parent in parent_cls:
            if issubclass(cls, parent) and cls != parent:
                return True
            
        return False

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
                    if self._is_strict_subclass(
                        model_cls,
                        LargeLanguageModel,
                        TextEmbeddingModel,
                        RerankModel,
                        TTSModel,
                        Speech2TextModel,
                        ModerationModel,
                    ):
                        models[model_cls.model_type] = model_cls(provider.models)

            provider_instance = cls(provider, models)
            self.models_mapping[provider.provider] = (provider, provider_instance, models)

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

    def get_model_provider_instance(self, provider: str):
        """
        get the model provider class by provider name
        :param provider: provider name
        :return: model provider class
        """
        for provider_registration in self.models_mapping:
            if provider_registration == provider:
                return self.models_mapping[provider_registration][1]

    def get_model_instance(self, provider: str, model_type: ModelType):
        """
        get the model class by provider
        :param provider: provider name
        :param model: model name
        :return: model class
        """
        for provider_registration in self.models_mapping:
            if provider_registration == provider:
                registration = self.models_mapping[provider_registration][2].get(
                    model_type
                )
                if registration:
                    return registration
