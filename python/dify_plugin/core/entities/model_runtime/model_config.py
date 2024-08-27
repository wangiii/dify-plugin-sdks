from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from dify_plugin.model.model_entities import ModelType


class BaseModelConfig(BaseModel):
    provider: str
    model: str
    model_type: ModelType

    model_config = ConfigDict(protected_namespaces=())


class LLMModelConfig(BaseModelConfig):
    """
    Model class for llm model config.
    """

    model_type: ModelType = ModelType.LLM
    mode: str
    model_parameters: dict[str, Any] = Field(default_factory=dict)


class TextEmbeddingModelConfig(BaseModelConfig):
    """
    Model class for text embedding model config.
    """

    model_type: ModelType = ModelType.TEXT_EMBEDDING


class RerankModelConfig(BaseModelConfig):
    """
    Model class for rerank model config.
    """

    model_type: ModelType = ModelType.RERANK
    score_threshold: float
    top_n: int


class TTSModelConfig(BaseModelConfig):
    """
    Model class for tts model config.
    """

    model_type: ModelType = ModelType.TTS
    voice: str


class Speech2TextModelConfig(BaseModelConfig):
    """
    Model class for speech2text model config.
    """

    model_type: ModelType = ModelType.SPEECH2TEXT


class ModerationModelConfig(BaseModelConfig):
    """
    Model class for moderation model config.
    """

    model_type: ModelType = ModelType.MODERATION
