import os
from abc import ABC, abstractmethod
from typing import Optional

from dify_plugin.model.ai_model import AIModel
from dify_plugin.model.model_entities import AIModelEntity, ModelType
from dify_plugin.model.provider_entities import ProviderEntity
from dify_plugin.utils.yaml_loader import load_yaml_file


class ModelProvider(ABC):
    provider_schema: Optional[ProviderEntity] = None
    model_instance_map: dict[str, AIModel] = {}

    @abstractmethod
    def validate_provider_credentials(self, credentials: dict) -> None:
        """
        Validate provider credentials
        You can choose any validate_credentials method of model type or implement validate method by yourself,
        such as: get model list api

        if validate failed, raise exception

        :param credentials: provider credentials, credentials form defined in `provider_credential_schema`.
        """
        raise NotImplementedError

    def get_provider_schema(self) -> ProviderEntity:
        """
        Get provider schema
    
        :return: provider schema
        """
        if self.provider_schema:
            return self.provider_schema
    
        # get dirname of the current path
        provider_name = self.__class__.__module__.split('.')[-1]

        # get the path of the model_provider classes
        base_path = os.path.abspath(__file__)
        current_path = os.path.join(os.path.dirname(os.path.dirname(base_path)), provider_name)
    
        # read provider schema from yaml file
        yaml_path = os.path.join(current_path, f'{provider_name}.yaml')
        yaml_data = load_yaml_file(yaml_path, ignore_error=True)
    
        try:
            # yaml_data to entity
            provider_schema = ProviderEntity(**yaml_data)
        except Exception as e:
            raise Exception(f'Invalid provider schema for {provider_name}: {str(e)}')

        # cache schema
        self.provider_schema = provider_schema
    
        return provider_schema

    def models(self, model_type: ModelType) -> list[AIModelEntity]:
        """
        Get all models for given model type

        :param model_type: model type defined in `ModelType`
        :return: list of models
        """
        provider_schema = self.get_provider_schema()
        if model_type not in provider_schema.supported_model_types:
            return []

        # get model instance of the model type
        model_instance = self.get_model_instance(model_type)

        # get predefined models (predefined_models)
        models = model_instance.predefined_models()

        # return models
        return models

    def get_model_instance(self, model_type: ModelType) -> AIModel:
        """
        Get model instance

        :param model_type: model type defined in `ModelType`
        :return:
        """
        model_type_str = model_type.value
        if model_type_str in self.model_instance_map:
            return self.model_instance_map[model_type_str]

        # get model class
        model_class = self._get_model_class(model_type)

        # create model instance
        model_instance = model_class()

        # cache model instance
        self.model_instance_map[model_type_str] = model_instance

        return model_instance