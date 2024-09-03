from pydantic import BaseModel
from dify_plugin.entities.model import BaseModelConfig, ModelType


class ModerationModelConfig(BaseModelConfig):
    """
    Model class for moderation model config.
    """

    model_type: ModelType = ModelType.MODERATION


class ModerationResult(BaseModel):
    """
    Model class for moderation result.
    """
    result: bool
