from pydantic import BaseModel


class TTSResult(BaseModel):
    """
    Model class for tts result.
    """
    result: str
