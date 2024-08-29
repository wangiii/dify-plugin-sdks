from enum import Enum
from pydantic import BaseModel, ConfigDict


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
    

class BaseModelConfig(BaseModel):
    provider: str
    model: str
    model_type: ModelType

    model_config = ConfigDict(protected_namespaces=())
