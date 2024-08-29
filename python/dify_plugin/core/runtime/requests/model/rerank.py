from dify_plugin.core.entities.model.rerank import RerankResult
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.model import BaseModelConfig, ModelType

class RerankModelConfig(BaseModelConfig):
    """
    Model class for rerank model config.
    """

    model_type: ModelType = ModelType.RERANK
    score_threshold: float
    top_n: int


class RerankRequest(DifyRequest[RerankResult]):
    def invoke(
        self, model_config: RerankModelConfig, docs: list[str], query: str
    ) -> RerankResult:
        """
        Invoke rerank
        """
        for data in self._backwards_invoke(
            InvokeType.Rerank,
            RerankResult,
            {
                **model_config.model_dump(),
                "docs": docs,
                "query": query,
            },
        ):
            return data

        raise Exception("No response from rerank")
