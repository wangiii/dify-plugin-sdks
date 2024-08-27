from enum import Enum

class CommonParameterType(Enum):
    SECRET_INPUT = "secret-input"
    TEXT_INPUT = "text-input"
    SELECT = "select"
    STRING = "string"
    NUMBER = "number"
    FILE = "file"
    BOOLEAN = "boolean"
    CHAT_APP_ID = "chat-app-id"
    COMPLETION_APP_ID = "completion-app-id"
    WORKFLOW_APP_ID = "workflow-app-id"
    MODEL_CONFIG = "model-config"
