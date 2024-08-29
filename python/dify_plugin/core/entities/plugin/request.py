from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, field_validator

from dify_plugin.core.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.model.model_entities import ModelType


class PluginInvokeType(Enum):
    Tool = "tool"
    Model = "model"
    Endpoint = "endpoint"


class ToolActions(Enum):
    ValidateCredentials = "validate_tool_credentials"
    InvokeTool = "invoke_tool"


class ModelActions(Enum):
    ValidateProviderCredentials = "validate_provider_credentials"
    ValidateModelCredentials = "validate_model_credentials"
    InvokeLLM = "invoke_llm"
    InvokeTextEmbedding = "invoke_text_embedding"
    InvokeRerank = "invoke_rerank"
    InvokeTTS = "invoke_tts"
    InvokeSpeech2Text = "invoke_speech2text"
    InvokeModeration = "invoke_moderation"


class EndpointActions(Enum):
    InvokeEndpoint = "invoke_endpoint"


class PluginAccessRequest(BaseModel):
    type: PluginInvokeType
    user_id: str


class ToolInvokeRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions = ToolActions.InvokeTool
    provider: str
    tool: str
    credentials: dict
    tool_parameters: dict[str, Any]


class ToolValidateCredentialsRequest(PluginAccessRequest):
    type: PluginInvokeType = PluginInvokeType.Tool
    action: ToolActions = ToolActions.ValidateCredentials
    provider: str
    credentials: dict


class PluginAccessModelRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    user_id: str
    provider: str
    model_type: ModelType
    model: str
    credentials: dict

    model_config = ConfigDict(protected_namespaces=())


class ModelInvokeLLMRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeLLM

    model_parameters: dict[str, Any]
    prompt_messages: list[PromptMessage]
    stop: Optional[list[str]]
    tools: Optional[list[PromptMessageTool]]
    stream: bool = True

    model_config = ConfigDict(protected_namespaces=())

    @field_validator("prompt_messages", mode="before")
    def convert_prompt_messages(cls, v):
        if not isinstance(v, list):
            raise ValueError("prompt_messages must be a list")

        for i in range(len(v)):
            if v[i]["role"] == PromptMessageRole.USER.value:
                v[i] = UserPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.ASSISTANT.value:
                v[i] = AssistantPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.SYSTEM.value:
                v[i] = SystemPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.TOOL.value:
                v[i] = ToolPromptMessage(**v[i])
            else:
                v[i] = PromptMessage(**v[i])

        return v


class ModelInvokeTextEmbeddingRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeTextEmbedding

    texts: list[str]


class ModelInvokeRerankRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeRerank

    query: str
    docs: list[str]
    score_threshold: Optional[float]
    top_n: Optional[int]


class ModelInvokeTTSRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeTTS

    content_text: str
    voice: str


class ModelInvokeSpeech2TextRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeSpeech2Text

    file: str


class ModelInvokeModerationRequest(PluginAccessModelRequest):
    action: ModelActions = ModelActions.InvokeModeration

    text: str


class ModelValidateProviderCredentialsRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    user_id: str
    provider: str
    credentials: dict

    action: ModelActions = ModelActions.ValidateProviderCredentials

    model_config = ConfigDict(protected_namespaces=())


class ModelValidateModelCredentialsRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Model
    user_id: str
    provider: str
    model_type: ModelType
    model: str
    credentials: dict

    action: ModelActions = ModelActions.ValidateModelCredentials

    model_config = ConfigDict(protected_namespaces=())


class EndpointInvokeRequest(BaseModel):
    type: PluginInvokeType = PluginInvokeType.Endpoint
    action: EndpointActions = EndpointActions.InvokeEndpoint
    raw_http_request: str
