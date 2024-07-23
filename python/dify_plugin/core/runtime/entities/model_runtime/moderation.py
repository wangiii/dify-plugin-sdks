from pydantic import BaseModel


class ModerationResult(BaseModel):
    """
    Model class for moderation result.
    """
    result: bool