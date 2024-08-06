import datetime
from enum import Enum

from pydantic import BaseModel


class PluginArch(Enum):
    AMD64 = "amd64"
    ARM64 = "arm64"


class PluginLanguage(Enum):
    PYTHON = "python"


class PluginType(Enum):
    Plugin = "plugin"


class PluginRunner(BaseModel):
    language: PluginLanguage
    version: str
    entrypoint: str


class PluginMeta(BaseModel):
    version: str
    arch: list[PluginArch]
    runner: dict


class PluginConfiguration(BaseModel):
    class Meta(BaseModel):
        class Arch(Enum):
            AMD64 = "amd64"
            ARM64 = "arm64"

    version: str
    type: PluginType
    author: str
    name: str
    created_at: datetime.datetime
    resource: dict
    plugins: list[str]
    meta: Meta


class PluginProviderType(Enum):
    Tool = "tool"
    Model = "model"
    Webhook = "webhook"
