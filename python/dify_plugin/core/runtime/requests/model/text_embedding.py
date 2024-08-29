from dify_plugin.core.entities.model.text_embedding import TextEmbeddingResult
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest



from dify_plugin.core.runtime.requests.model import BaseModelConfig, ModelType


class TextEmbeddingModelConfig(BaseModelConfig):
    """
    Model class for text embedding model config.
    """

    model_type: ModelType = ModelType.TEXT_EMBEDDING



class TextEmbeddingRequest(DifyRequest[TextEmbeddingResult]):
    def invoke(
        self, model_config: TextEmbeddingResult, texts: list[str]
    ) -> TextEmbeddingResult:
        """
        Invoke text embedding
        """
        for data in self._backwards_invoke(
            InvokeType.TextEmbedding,
            TextEmbeddingResult,
            {
                **model_config.model_dump(),
                "texts": texts,
            },
        ):
            return data

        raise Exception("No response from text embedding")
