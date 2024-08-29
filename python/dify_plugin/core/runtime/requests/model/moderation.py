from pydantic import BaseModel
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.model import BaseModelConfig, ModelType


class ModerationModelConfig(BaseModelConfig):
    """
    Model class for moderation model config.
    """

    model_type: ModelType = ModelType.MODERATION


class ModerationResult(BaseModel):
    """
    Model class for moderation result.
    """
    result: bool


class ModerationRequest(DifyRequest[ModerationResult]):
    def invoke(self, model_config: ModerationModelConfig, text: str) -> bool:
        """
        Invoke moderation
        """
        for data in self._backwards_invoke(
            InvokeType.Moderation,
            ModerationResult,
            {
                **model_config.model_dump(),
                "text": text,
            },
        ):
            return data.result

        raise Exception("No response from moderation")
