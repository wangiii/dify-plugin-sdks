from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dify_plugin.core.entities.plugin.common import I18nObject
from dify_plugin.model.parameter_template import PARAMETER_RULE_TEMPLATE, DefaultParameterName


class ModelType(Enum):
    """
    Enum class for model type.
    """
    LLM = "llm"
    TEXT_EMBEDDING = "text-embedding"
    RERANK = "rerank"
    SPEECH2TEXT = "speech2text"
    MODERATION = "moderation"
    TTS = "tts"
    TEXT2IMG = "text2img"

class FetchFrom(Enum):
    """
    Enum class for fetch from.
    """
    PREDEFINED_MODEL = "predefined-model"
    CUSTOMIZABLE_MODEL = "customizable-model"


class ModelFeature(Enum):
    """
    Enum class for llm feature.
    """
    TOOL_CALL = "tool-call"
    MULTI_TOOL_CALL = "multi-tool-call"
    AGENT_THOUGHT = "agent-thought"
    VISION = "vision"
    STREAM_TOOL_CALL = "stream-tool-call"


class ParameterType(Enum):
    """
    Enum class for parameter type.
    """
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"


class ModelPropertyKey(Enum):
    """
    Enum class for model property key.
    """
    MODE = "mode"
    CONTEXT_SIZE = "context_size"
    MAX_CHUNKS = "max_chunks"
    FILE_UPLOAD_LIMIT = "file_upload_limit"
    SUPPORTED_FILE_EXTENSIONS = "supported_file_extensions"
    MAX_CHARACTERS_PER_CHUNK = "max_characters_per_chunk"
    DEFAULT_VOICE = "default_voice"
    VOICES = "voices"
    WORD_LIMIT = "word_limit"
    AUDIO_TYPE = "audio_type"
    MAX_WORKERS = "max_workers"


class ProviderModel(BaseModel):
    """
    Model class for provider model.
    """
    model: str
    label: I18nObject
    model_type: ModelType
    features: Optional[list[ModelFeature]] = None
    fetch_from: FetchFrom = Field(default=FetchFrom.PREDEFINED_MODEL)
    model_properties: dict[ModelPropertyKey, Any]
    deprecated: bool = False
    model_config = ConfigDict(protected_namespaces=())

    """
        use model as label
    """
    @model_validator(mode='before')
    def validate_label(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if not data.get("label"):
                data["label"] = I18nObject(en_US=data["model"])
        
        return data

class ParameterRule(BaseModel):
    """
    Model class for parameter rule.
    """
    name: str
    use_template: Optional[str] = None
    label: I18nObject
    type: ParameterType
    help: Optional[I18nObject] = None
    required: bool = False
    default: Optional[Any] = None
    min: Optional[float] = None
    max: Optional[float] = None
    precision: Optional[int] = None
    options: list[str] = []

    @model_validator(mode='before')
    def validate_label(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if not data.get("label"):
                data["label"] = I18nObject(en_US=data["name"])

            # check if there is a template
            if 'use_template' in data:
                try:
                    default_parameter_name = DefaultParameterName.value_of(data['use_template'])
                    default_parameter_rule = PARAMETER_RULE_TEMPLATE.get(default_parameter_name)
                    if not default_parameter_rule:
                        raise Exception(f"Invalid model parameter rule name {default_parameter_name}")
                    copy_default_parameter_rule = default_parameter_rule.copy()
                    copy_default_parameter_rule.update(data)
                    data = copy_default_parameter_rule
                except ValueError:
                    pass
        
        return data

class PriceConfig(BaseModel):
    """
    Model class for pricing info.
    """
    input: Decimal
    output: Optional[Decimal] = None
    unit: Decimal
    currency: str


class AIModelEntity(ProviderModel):
    """
    Model class for AI model.
    """
    parameter_rules: list[ParameterRule] = []
    pricing: Optional[PriceConfig] = None


class ModelUsage(BaseModel):
    pass


class PriceType(Enum):
    """
    Enum class for price type.
    """
    INPUT = "input"
    OUTPUT = "output"


class PriceInfo(BaseModel):
    """
    Model class for price info.
    """
    unit_price: Decimal
    unit: Decimal
    total_amount: Decimal
    currency: str
