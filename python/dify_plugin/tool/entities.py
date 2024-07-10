from pydantic import BaseModel

class ToolConfiguration(BaseModel):
    name: str

class ToolProviderConfiguration(BaseModel):
    name: str

class ToolRuntime(BaseModel):
    credentials: dict
