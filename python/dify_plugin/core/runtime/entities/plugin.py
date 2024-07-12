import datetime
from enum import Enum
from dateutil import parser
from pydantic import BaseModel, field_validator

"""
version: 0.0.1
author: "Yeuoly"
name: "Google"
created_at: "2024-07-12T08:03:44.658609186Z"
resource:
  memory: 1048576
  storage: 1048576
  permission:
    tool:
      enabled: true
    model:
      enabled: true
      llm: true
plugins:
  - "provider/google.yaml"
meta:
  version: 0.0.1
  arch:
    - "amd64"
    - "arm64"
  runner:
    language: "python"
    version: "3.12"
    entrypoint: "main"

"""

class PluginArch(Enum):
    AMD64 = "amd64"
    ARM64 = "arm64"

class PluginLanguage(Enum):
    PYTHON = "python"

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
    author: str
    name: str
    created_at: datetime.datetime
    resource: dict
    plugins: list[str]
    meta: Meta
