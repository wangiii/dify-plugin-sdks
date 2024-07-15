from enum import Enum


class ToolProviderType(Enum):
    """
        Enum class for tool provider
    """
    BUILT_IN = "builtin"
    WORKFLOW = "workflow"
    API = "api"
    APP = "app"
    DATASET_RETRIEVAL = "dataset-retrieval"

    @classmethod
    def value_of(cls, value: str) -> 'ToolProviderType':
        """
        Get value of given mode.

        :param value: mode value
        :return: mode
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f'invalid mode value {value}')