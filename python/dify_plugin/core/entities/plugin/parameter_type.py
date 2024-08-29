from enum import Enum

class CommonParameterType(Enum):
    SECRET_INPUT = "secret-input"
    TEXT_INPUT = "text-input"
    SELECT = "select"
    STRING = "string"
    NUMBER = "number"
    FILE = "file"
    BOOLEAN = "boolean"
    CHAT_APP = "chat-app"
    COMPLETION_APP = "completion-app"
    WORKFLOW_APP = "workflow-app"
    MODEL_CONFIG = "model-config"


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
