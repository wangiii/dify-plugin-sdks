from pydantic import BaseModel
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.workflow_node import NodeResponse, NodeType


class QuestionClassifierNodeData(BaseModel):
    pass


class QuestionClassifierNodeRequest(DifyRequest[NodeResponse]):
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
