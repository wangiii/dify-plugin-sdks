from binascii import hexlify
from typing import IO

from pydantic import BaseModel
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.model import BaseModelConfig, ModelType


class Speech2TextModelConfig(BaseModelConfig):
    """
    Model class for speech2text model config.
    """

    model_type: ModelType = ModelType.SPEECH2TEXT

    
class Speech2TextResult(BaseModel):
    """
    Model class for rerank result.
    """
    result: str

    
class Speech2TextRequest(DifyRequest[Speech2TextResult]):
    def invoke(
        self, model_config: Speech2TextModelConfig, file: IO[bytes]
    ) -> str:
        """
        Invoke speech2text
        """
        for data in self._backwards_invoke(
            InvokeType.Speech2Text,
            Speech2TextResult,
            {
                **model_config.model_dump(),
                "file": hexlify(file.read()),
            },
        ):
            return data.result

        raise Exception("No response from speech2text")
