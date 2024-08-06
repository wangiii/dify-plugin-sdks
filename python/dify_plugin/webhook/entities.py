from pydantic import BaseModel


class WebhookConfigurationExtra(BaseModel):
    class Python(BaseModel):
        source: str

    python: Python


class WebhookConfiguration(BaseModel):
    path: str
    method: str
    extra: WebhookConfigurationExtra
