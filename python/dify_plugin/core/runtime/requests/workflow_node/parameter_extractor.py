from pydantic import BaseModel
from dify_plugin.core.entities.plugin.invocation import InvokeType
from dify_plugin.core.runtime.requests import DifyRequest
from dify_plugin.core.runtime.requests.workflow_node import NodeResponse, NodeType


class ParameterExtractorNodeData(BaseModel):
    pass


class ParameterExtractorNodeRequest(DifyRequest[NodeResponse]):
    def invoke(
        self,
        node_data: ParameterExtractorNodeData, 
        inputs: dict
    ) -> NodeResponse:
        """
        Invoke Parameter Extractor Node
        """
        response = self._backwards_invoke(
            InvokeType.Node,
            NodeResponse,
            {
                "node_type": NodeType.PARAMETER_EXTRACTOR,
                "node_data": node_data,
                "inputs": inputs,
            },
        )

        for data in response:
            return data

        raise Exception("No response from workflow node parameter extractor")