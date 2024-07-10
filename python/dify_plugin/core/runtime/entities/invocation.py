from enum import Enum


class InvokeType(Enum):
    Tool = 'tool'
    Model = 'model'
    Node = 'node'

    @classmethod
    def value_of(cls, value: str) -> 'InvokeType':
        """
        Get value of given mode.

        :param value: type
        :return: mode
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f'invalid type value {value}')
