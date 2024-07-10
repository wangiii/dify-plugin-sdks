from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict


class DifyPluginConfig(BaseModel):
    MAX_REQUEST_TIMEOUT: int = 300

    model_config = SettingsConfigDict(
        # read from dotenv format config file
        env_file='.env',
        env_file_encoding='utf-8',
        frozen=True,

        # ignore extra attributes
        extra='ignore',
    )

dify_plugin_config = DifyPluginConfig()