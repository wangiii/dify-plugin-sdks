from pydantic import BaseModel


class LLMResultChunk(BaseModel):
    pass

class TextEmbeddingResult(BaseModel):
    pass

class RerankResult(BaseModel):
    pass