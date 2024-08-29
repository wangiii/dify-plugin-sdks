from typing import Any, Optional, Union
from pydantic import BaseModel, Field, RootModel, field_validator, model_validator
from enum import Enum

from dify_plugin.core.entities.plugin.common import I18nObject
from dify_plugin.core.entities.plugin.parameter_type import (
    AppSelectorScope,
    CommonParameterType,
    ModelConfigScope,
)
from dify_plugin.utils.yaml_loader import load_yaml_file


class ToolRuntime(BaseModel):
    credentials: dict[str, str]
    user_id: Optional[str]
    session_id: Optional[str]


class ToolInvokeMessage(BaseModel):
    class TextMessage(BaseModel):
        text: str

        def to_dict(self):
            return {"text": self.text}

    class JsonMessage(BaseModel):
        json_object: dict

        def to_dict(self):
            return {"json_object": self.json_object}

    class MessageType(Enum):
        TEXT = "text"
        FILE = "file"
        BLOB = "blob"
        JSON = "json"

    type: MessageType
    message: TextMessage | JsonMessage

    def to_dict(self):
        return {"type": self.type.value, "message": self.message.to_dict()}


class ToolIdentity(BaseModel):
    author: str = Field(..., description="The author of the tool")
    name: str = Field(..., description="The name of the tool")
    label: I18nObject = Field(..., description="The label of the tool")


class ToolParameterOption(BaseModel):
    value: str = Field(..., description="The value of the option")
    label: I18nObject = Field(..., description="The label of the option")

    @field_validator("value", mode="before")
    @classmethod
    def transform_id_to_str(cls, value) -> str:
        if not isinstance(value, str):
            return str(value)
        else:
            return value


class ToolParameter(BaseModel):
    class ToolParameterType(str, Enum):
        STRING = CommonParameterType.STRING.value
        NUMBER = CommonParameterType.NUMBER.value
        BOOLEAN = CommonParameterType.BOOLEAN.value
        SELECT = CommonParameterType.SELECT.value
        SECRET_INPUT = CommonParameterType.SECRET_INPUT.value
        FILE = CommonParameterType.FILE.value
        MODEL_CONFIG = CommonParameterType.MODEL_CONFIG.value
        CHAT_APP_ID = CommonParameterType.CHAT_APP.value
        COMPLETION_APP_ID = CommonParameterType.COMPLETION_APP.value
        WORKFLOW_APP_ID = CommonParameterType.WORKFLOW_APP.value

    class ToolParameterForm(Enum):
        SCHEMA = "schema"  # should be set while adding tool
        FORM = "form"  # should be set before invoking tool
        LLM = "llm"  # will be set by LLM

    name: str = Field(..., description="The name of the parameter")
    label: I18nObject = Field(..., description="The label presented to the user")
    human_description: I18nObject = Field(
        ..., description="The description presented to the user"
    )
    type: ToolParameterType = Field(..., description="The type of the parameter")
    scope: Optional[AppSelectorScope | ModelConfigScope] = None
    form: ToolParameterForm = Field(
        ..., description="The form of the parameter, schema/form/llm"
    )
    llm_description: Optional[str] = None
    required: Optional[bool] = False
    default: Optional[Union[int, str]] = None
    min: Optional[Union[float, int]] = None
    max: Optional[Union[float, int]] = None
    options: Optional[list[ToolParameterOption]] = None


class ToolDescription(BaseModel):
    human: I18nObject = Field(..., description="The description presented to the user")
    llm: str = Field(..., description="The description presented to the LLM")


class ToolConfigurationExtra(BaseModel):
    class Python(BaseModel):
        source: str

    python: Python


class ToolOutputSchema(RootModel):
    root: dict[str, Any]


class ToolConfiguration(BaseModel):
    identity: ToolIdentity
    parameters: list[ToolParameter] = Field(
        default=[], description="The parameters of the tool"
    )
    description: ToolDescription
    extra: ToolConfigurationExtra
    output_schema: Optional[ToolOutputSchema] = Field(default_factory=dict)


class ToolLabelEnum(Enum):
    SEARCH = "search"
    IMAGE = "image"
    VIDEOS = "videos"
    WEATHER = "weather"
    FINANCE = "finance"
    DESIGN = "design"
    TRAVEL = "travel"
    SOCIAL = "social"
    NEWS = "news"
    MEDICAL = "medical"
    PRODUCTIVITY = "productivity"
    EDUCATION = "education"
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    OTHER = "other"


class ToolCredentialsOption(BaseModel):
    value: str = Field(..., description="The value of the option")
    label: I18nObject = Field(..., description="The label of the option")


class ProviderConfig(BaseModel):
    class Config(Enum):
        SECRET_INPUT = CommonParameterType.SECRET_INPUT.value
        TEXT_INPUT = CommonParameterType.TEXT_INPUT.value
        SELECT = CommonParameterType.SELECT.value
        BOOLEAN = CommonParameterType.BOOLEAN.value
        MODEL_CONFIG = CommonParameterType.MODEL_CONFIG.value
        CHAT_APP_ID = CommonParameterType.CHAT_APP.value
        COMPLETION_APP_ID = CommonParameterType.COMPLETION_APP.value
        WORKFLOW_APP_ID = CommonParameterType.WORKFLOW_APP.value

        @classmethod
        def value_of(cls, value: str) -> "ProviderConfig.Config":
            """
            Get value of given mode.

            :param value: mode value
            :return: mode
            """
            for mode in cls:
                if mode.value == value:
                    return mode
            raise ValueError(f"invalid mode value {value}")

    name: str = Field(..., description="The name of the credentials")
    type: Config = Field(..., description="The type of the credentials")
    required: bool = False
    default: Optional[Union[int, float, str]] = None
    options: Optional[list[ToolCredentialsOption]] = None
    label: I18nObject
    help: Optional[I18nObject] = None
    url: Optional[str] = None
    placeholder: Optional[I18nObject] = None


class ToolProviderIdentity(BaseModel):
    author: str = Field(..., description="The author of the tool")
    name: str = Field(..., description="The name of the tool")
    description: I18nObject = Field(..., description="The description of the tool")
    icon: str = Field(..., description="The icon of the tool")
    label: I18nObject = Field(..., description="The label of the tool")
    tags: list[ToolLabelEnum] = Field(
        default=[],
        description="The tags of the tool",
    )


class ToolProviderConfigurationExtra(BaseModel):
    class Python(BaseModel):
        source: str

    python: Python


class ToolProviderConfiguration(BaseModel):
    identity: ToolProviderIdentity
    credentials_schema: dict[str, ProviderConfig] = Field(
        alias="credentials_for_provider",
        default={},
        description="The credentials schema of the tool provider",
    )
    tools: list[ToolConfiguration] = Field(
        default=[], description="The tools of the tool provider"
    )
    extra: ToolProviderConfigurationExtra

    @model_validator(mode="before")
    def validate_credentials_schema(cls, data: dict) -> dict:
        credentials_for_provider: dict[str, Any] = data.get(
            "credentials_for_provider", {}
        )
        for credential in credentials_for_provider:
            credentials_for_provider[credential]["name"] = credential

        data["credentials_for_provider"] = credentials_for_provider
        return data

    @field_validator("tools", mode="before")
    def validate_tools(cls, value) -> list[ToolConfiguration]:
        if not isinstance(value, list):
            raise ValueError("tools should be a list")

        tools: list[ToolConfiguration] = []

        for tool in value:
            # read from yaml
            if not isinstance(tool, str):
                raise ValueError("tool path should be a string")
            try:
                file = load_yaml_file(tool)
                tools.append(
                    ToolConfiguration(
                        **{
                            "identity": ToolIdentity(**file["identity"]),
                            "parameters": [
                                ToolParameter(**param)
                                for param in file.get("parameters", [])
                            ],
                            "description": ToolDescription(**file["description"]),
                            "extra": ToolConfigurationExtra(**file.get("extra", {})),
                        }
                    )
                )
            except Exception as e:
                raise ValueError(f"Error loading tool configuration: {str(e)}")

        return tools
