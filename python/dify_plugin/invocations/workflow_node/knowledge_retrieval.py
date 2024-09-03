from dify_plugin.entities.workflow_node import KnowledgeRetrievalNodeData, NodeResponse, NodeType
from dify_plugin.core.entities.invocation import InvokeType
from dify_plugin.core.runtime import BackwardsInvocation


class KnowledgeRetrievalNodeInvocation(BackwardsInvocation[NodeResponse]):
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