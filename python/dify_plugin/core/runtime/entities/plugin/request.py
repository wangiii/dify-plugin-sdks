from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel

from dify_plugin.core.runtime.entities.model_runtime.message import PromptMessage, PromptMessageTool
from dify_plugin.model.model_entities import ModelType

class PluginInvokeType(Enum):
    Tool = 'tool'
    Model = 'model'

class ToolActions(Enum):
    ValidateCredentials = 'validate_credentials'
    Invoke = 'invoke'

class ModelActions(Enum):
    ValidateProviderCredentials = 'validate_provider_credentials'
    ValidateModelCredentials = 'validate_model_credentials'
    Invoke = 'invoke'

class PluginInvokeRequest(BaseModel):
    type: PluginInvokeType
    user_id: str

class ToolInvokeRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions = ToolActions.Invoke
    provider: str
    tool: str
    credentials: dict
    parameters: dict[str, Any]

class ToolValidateCredentialsRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions = ToolActions.ValidateCredentials
    provider: str
    credentials: dict

class PluginAccessToolRequest(PluginInvokeRequest):
    type: PluginInvokeType = PluginInvokeType.Tool
    data: ToolInvokeRequest | ToolValidateCredentialsRequest

class ModelInvokeRequest(BaseModel):
    action: ModelActions = ModelActions.Invoke
    provider: str
    model_type: ModelType
    model: str
    credentials: dict
    model_parameters: dict[str, Any]
    prompt_messages: list[PromptMessage]
    tools: Optional[list[PromptMessageTool]]
    stream: bool = True

class ModelValidateProviderCredentialsRequest(BaseModel):
    action: ModelActions = ModelActions.ValidateProviderCredentials
    provider: str
    credentials: dict

class ModelValidateModelCredentialsRequest(BaseModel):
    action: ModelActions = ModelActions.ValidateModelCredentials
    provider: str
    model: str
    credentials: dict

class PluginAccessModelRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    data: ModelInvokeRequest | ModelValidateProviderCredentialsRequest | ModelValidateModelCredentialsRequest