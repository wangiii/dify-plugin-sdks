from ...core.entities.invocation import InvokeType
from ...core.runtime import BackwardsInvocation
from ...entities.workflow_node import NodeResponse, NodeType, QuestionClassifierNodeData


class QuestionClassifierNodeInvocation(BackwardsInvocation[NodeResponse]):
    def invoke(
        self,
        node_data: QuestionClassifierNodeData, 
        inputs: dict
    ) -> NodeResponse:
        """
        Invoke Question Classifier Node
        """
        response = self._backwards_invoke(
            InvokeType.Node,
            NodeResponse,
            {
                "node_type": NodeType.QUESTION_CLASSIFIER,
                "node_data": node_data,
                "inputs": inputs,
            },
        )

        for data in response:
            return data

        raise Exception("No response from workflow node question classifier")
