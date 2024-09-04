import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from dify_plugin.core.entities.plugin.common import I18nObject


class PluginArch(Enum):
    AMD64 = "amd64"
    ARM64 = "arm64"


class PluginLanguage(Enum):
    PYTHON = "python"


class PluginType(Enum):
    Plugin = "plugin"


class PluginResourceRequirements(BaseModel):
    memory: int

    class Permission(BaseModel):
        class Tool(BaseModel):
            enabled: bool

        class Model(BaseModel):
            enabled: Optional[bool]
            llm: Optional[bool]
            text_embedding: Optional[bool]
            rerank: Optional[bool]
            tts: Optional[bool]
            speech2text: Optional[bool]
            moderation: Optional[bool]

        class Node(BaseModel):
            enabled: bool

        class Endpoint(BaseModel):
            enabled: bool

        class Storage(BaseModel):
            enabled: bool
            size: int = Field(ge=1024, le=1073741824)

        tool: Optional[Tool]
        model: Optional[Model]
        node: Optional[Node]
        endpoint: Optional[Endpoint]
        storage: Storage

    permission: Permission


class PluginConfiguration(BaseModel):
    class Meta(BaseModel):
        class PluginRunner(BaseModel):
            language: PluginLanguage
            version: str
            entrypoint: str

        version: str
        arch: list[PluginArch]
        runner: PluginRunner

    version: str
    type: PluginType
    author: str
    name: str
    icon: str
    label: I18nObject
    created_at: datetime.datetime
    resource: dict
    plugins: list[str]
    meta: Meta


class PluginProviderType(Enum):
    Tool = "tool"
    Model = "model"
    Endpoint = "endpoint"


class PluginAsset(BaseModel):
    filename: str
    data: str # hex encoded file data
    