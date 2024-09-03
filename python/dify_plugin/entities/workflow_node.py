from enum import Enum
from pydantic import BaseModel


class NodeResponse(BaseModel):
    pass


class NodeType(str, Enum):
    """
    Node Types.
    """

    START = 'start'
    END = 'end'
    ANSWER = 'answer'
    LLM = 'llm'
    KNOWLEDGE_RETRIEVAL = 'knowledge-retrieval'
    IF_ELSE = 'if-else'
    CODE = 'code'
    TEMPLATE_TRANSFORM = 'template-transform'
    QUESTION_CLASSIFIER = 'question-classifier'
    HTTP_REQUEST = 'http-request'
    TOOL = 'tool'
    VARIABLE_AGGREGATOR = 'variable-aggregator'
    LOOP = 'loop'
    ITERATION = 'iteration'
    PARAMETER_EXTRACTOR = 'parameter-extractor'
    CONVERSATION_VARIABLE_ASSIGNER = 'assigner'

    @classmethod
    def value_of(cls, value: str) -> 'NodeType':
        """
        Get value of given node type.

        :param value: node type value
        :return: node type
        """
        for node_type in cls:
            if node_type.value == value:
                return node_type
        raise ValueError(f'invalid node type value {value}')


class QuestionClassifierNodeData(BaseModel):
    pass


class ParameterExtractorNodeData(BaseModel):
    pass


class KnowledgeRetrievalNodeData(BaseModel):
    pass
