import base64
from typing import Any, Optional, Union
from pydantic import (
    BaseModel,
    Field,
    RootModel,
    field_serializer,
    field_validator,
    model_validator,
)
from enum import Enum

from ..entities import I18nObject
from ..core.utils.yaml_loader import load_yaml_file


class CommonParameterType(Enum):
    SECRET_INPUT = "secret-input"
    TEXT_INPUT = "text-input"
    SELECT = "select"
    STRING = "string"
    NUMBER = "number"
    FILE = "file"
    BOOLEAN = "boolean"
    APP_SELECTOR = "app-selector"
    MODEL_SELECTOR = "model-selector"
    TOOL_SELECTOR = "tool-selector"


class AppSelectorScope(Enum):
    ALL = "all"
    CHAT = "chat"
    WORKFLOW = "workflow"
    COMPLETION = "completion"


class ModelConfigScope(Enum):
    LLM = "llm"
    TEXT_EMBEDDING = "text-embedding"
    RERANK = "rerank"
    TTS = "tts"
    SPEECH2TEXT = "speech2text"
    MODERATION = "moderation"
    VISION = "vision"


class ToolSelectorScope(Enum):
    ALL = "all"
    PLUGIN = "plugin"
    API = "api"
    WORKFLOW = "workflow"


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

    class BlobMessage(BaseModel):
        blob: bytes

    class BlobChunkMessage(BaseModel):
        id: str = Field(..., description="The id of the blob")
        sequence: int = Field(..., description="The sequence of the chunk")
        total_length: int = Field(..., description="The total length of the blob")
        blob: bytes = Field(..., description="The blob data of the chunk")
        end: bool = Field(..., description="Whether the chunk is the last chunk")

    class VariableMessage(BaseModel):
        variable_name: str = Field(
            ...,
            description="The name of the variable, only supports root-level variables",
        )
        variable_value: Any = Field(..., description="The value of the variable")
        stream: bool = Field(
            default=False, description="Whether the variable is streamed"
        )

        @field_validator("variable_value", "stream")
        @classmethod
        def validate_variable_value_and_stream(cls, v, values):
            if "stream" in values and values["stream"]:
                if not isinstance(v, str):
                    raise ValueError(
                        "When 'stream' is True, 'variable_value' must be a string."
                    )
            return v

    class MessageType(Enum):
        TEXT = "text"
        FILE = "file"
        BLOB = "blob"
        JSON = "json"
        LINK = "link"
        IMAGE = "image"
        IMAGE_LINK = "image_link"
        VARIABLE = "variable"
        BLOB_CHUNK = "blob_chunk"

    type: MessageType
    message: (
        TextMessage
        | JsonMessage
        | VariableMessage
        | BlobMessage
        | BlobChunkMessage
        | None
    )
    meta: Optional[dict] = None

    @field_validator("message", mode="before")
    @classmethod
    def decode_blob_message(cls, v):
        if isinstance(v, dict) and "blob" in v:
            try:
                v["blob"] = base64.b64decode(v["blob"])
            except Exception:
                pass
        return v

    @field_serializer("message")
    def serialize_message(self, v):
        if isinstance(v, self.BlobMessage):
            return {"blob": base64.b64encode(v.blob).decode("utf-8")}
        elif isinstance(v, self.BlobChunkMessage):
            return {
                "id": v.id,
                "sequence": v.sequence,
                "total_length": v.total_length,
                "blob": base64.b64encode(v.blob).decode("utf-8"),
                "end": v.end,
            }
        return v


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
        MODEL_SELECTOR = CommonParameterType.MODEL_SELECTOR.value
        APP_SELECTOR = CommonParameterType.APP_SELECTOR.value
        TOOL_SELECTOR = CommonParameterType.TOOL_SELECTOR.value

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
    scope: Optional[AppSelectorScope | ModelConfigScope | ToolSelectorScope] = None
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
    has_runtime_parameters: bool = Field(
        default=False, description="Whether the tool has runtime parameters"
    )
    output_schema: Optional[ToolOutputSchema] = None


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
        MODEL_SELECTOR = CommonParameterType.MODEL_SELECTOR.value
        APP_SELECTOR = CommonParameterType.APP_SELECTOR.value
        TOOL_SELECTOR = CommonParameterType.TOOL_SELECTOR.value

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
    scope: Optional[AppSelectorScope | ModelConfigScope | ToolSelectorScope] = None
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
    credentials_schema: list[ProviderConfig] = Field(
        default_factory=list,
        alias="credentials_for_provider",
        description="The credentials schema of the tool provider",
    )
    tools: list[ToolConfiguration] = Field(
        default=[], description="The tools of the tool provider"
    )
    extra: ToolProviderConfigurationExtra

    @model_validator(mode="before")
    def validate_credentials_schema(cls, data: dict) -> dict:
        original_credentials_for_provider: dict[str, dict] = data.get(
            "credentials_for_provider", {}
        )

        credentials_for_provider: list[dict[str, Any]] = []
        for name, credential in original_credentials_for_provider.items():
            credential["name"] = name
            credentials_for_provider.append(credential)

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
                                for param in file.get("parameters", []) or []
                            ],
                            "description": ToolDescription(**file["description"]),
                            "extra": ToolConfigurationExtra(**file.get("extra", {})),
                        }
                    )
                )
            except Exception as e:
                raise ValueError(f"Error loading tool configuration: {str(e)}")

        return tools


class ToolProviderType(Enum):
    """
    Enum class for tool provider
    """

    BUILT_IN = "builtin"
    WORKFLOW = "workflow"
    API = "api"
    APP = "app"
    DATASET_RETRIEVAL = "dataset-retrieval"

    @classmethod
    def value_of(cls, value: str) -> "ToolProviderType":
        """
        Get value of given mode.

        :param value: mode value
        :return: mode
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"invalid mode value {value}")
