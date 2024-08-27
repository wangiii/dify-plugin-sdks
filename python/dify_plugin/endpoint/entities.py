from typing import Optional
from pydantic import BaseModel

from dify_plugin.model.provider_entities import ProviderConfig


class EndpointConfigurationExtra(BaseModel):
    class Python(BaseModel):
        source: str

    python: Python


class EndpointConfiguration(BaseModel):
    path: str
    method: str
    settings: Optional[ProviderConfig] = None
    extra: EndpointConfigurationExtra
