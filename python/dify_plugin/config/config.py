from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict


class DifyPluginConfig(BaseModel):
    MAX_REQUEST_TIMEOUT: int = Field(default=300, description='Maximum request timeout in seconds')
    MAX_WORKER: int = Field(default=10, description='Maximum worker count')

    model_config = SettingsConfigDict(
        # read from dotenv format config file
        env_file='.env',
        env_file_encoding='utf-8',
        frozen=True,

        # ignore extra attributes
        extra='ignore',
    )
