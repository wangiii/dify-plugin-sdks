from ...entities.model.text_embedding import TextEmbeddingResult
from ...core.entities.invocation import InvokeType
from ...core.runtime import BackwardsInvocation


class TextEmbeddingInvocation(BackwardsInvocation[TextEmbeddingResult]):
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
