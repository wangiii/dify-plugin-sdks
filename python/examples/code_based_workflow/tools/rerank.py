from collections.abc import Generator

from dify_plugin.entities.model.rerank import RerankModelConfig
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.interfaces.tool import Tool


class Rerank(Tool):
    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        response = self.session.model.rerank.invoke(
            model_config=RerankModelConfig(
                provider="jina",
                model="jina-embeddings-v2-base-v1.0",
                score_threshold=0.5,
                top_n=10,
            ),
            docs=["Kasumi", "Utae", "Arisa"],
            query="Utae",
        )

        yield self.create_json_message(
            {
                "data": response.docs,
            }
        )
