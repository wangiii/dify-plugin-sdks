from pydantic import BaseModel


class EndpointConfigurationExtra(BaseModel):
    class Python(BaseModel):
        source: str

    python: Python


class EndpointConfiguration(BaseModel):
    path: str
    method: str
    extra: EndpointConfigurationExtra
