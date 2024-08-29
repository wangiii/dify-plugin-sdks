from binascii import unhexlify
from collections.abc import Generator

from pydantic import BaseModel
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.model import BaseModelConfig, ModelType


class TTSModelConfig(BaseModelConfig):
    """
    Model class for tts model config.
    """

    model_type: ModelType = ModelType.TTS
    voice: str

class TTSResult(BaseModel):
    """
    Model class for tts result.
    """
    result: str

    
class TTSRequest(DifyRequest[TTSResult]):
    def invoke(
        self, model_config: TTSModelConfig, content_text: str
    ) -> Generator[bytes, None, None]:
        """
        Invoke tts
        """
        for data in self._backwards_invoke(
            InvokeType.TTS,
            TTSResult,
            {
                **model_config.model_dump(),
                "content_text": content_text,
            },
        ):
            yield unhexlify(data.result)