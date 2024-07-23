from openai import BaseModel


class Speech2TextResult(BaseModel):
    """
    Model class for rerank result.
    """
    result: str
