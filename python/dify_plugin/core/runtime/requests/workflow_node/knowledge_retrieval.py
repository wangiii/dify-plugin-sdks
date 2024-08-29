from pydantic import BaseModel
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.workflow_node import NodeResponse, NodeType


class KnowledgeRetrievalNodeData(BaseModel):
    pass


class KnowledgeRetrievalNodeRequest(DifyRequest[NodeResponse]):
    def invoke(
        self,
        node_data: KnowledgeRetrievalNodeData, 
        inputs: dict
    ) -> NodeResponse:
        """
        Invoke Knowledge Retrieval Node
        """
        response = self._backwards_invoke(
            InvokeType.Node,
            NodeResponse,
            {
                "node_type": NodeType.KNOWLEDGE_RETRIEVAL,
                "node_data": node_data,
                "inputs": inputs,
            },
        )

        for data in response:
            return data

        raise Exception("No response from workflow node knowledge retrieval")