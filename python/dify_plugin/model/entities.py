from pydantic import BaseModel, ConfigDict, Field
from dify_plugin.model.provider_entities import ProviderEntity

class ModelProviderConfigurationExtra(BaseModel):
    class Python(BaseModel):
        provider_source: str
        model_sources: list[str] = Field(default_factory=list)

        model_config = ConfigDict(protected_namespaces=())

    python: Python

class ModelProviderConfiguration(ProviderEntity):
    extra: ModelProviderConfigurationExtra
