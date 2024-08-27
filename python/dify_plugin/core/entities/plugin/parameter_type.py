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
