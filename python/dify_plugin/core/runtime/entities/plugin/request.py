from enum import Enum
from typing import Any
from pydantic import BaseModel

class PluginInvokeType(Enum):
    Tool = 'tool'
    Model = 'model'

class ToolActions(Enum):
    ValidateCredentials = 'validate_credentials'
    Invoke = 'invoke'

class ModelActions(Enum):
    ValidateCredentials = 'validate_credentials'
    Invoke = 'invoke'

class PluginInvokeRequest(BaseModel):
    type: PluginInvokeType
    user_id: str

class ToolInvokeRequest(PluginInvokeRequest):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions
    provider: str
    tool: str
    credentials: dict
    parameters: dict[str, Any]

class ModelInvokeRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    action: ModelActions
    provider: str
    model: str
    credentials: dict
    parameters: dict[str, Any]
