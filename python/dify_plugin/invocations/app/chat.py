from collections.abc import Generator
from typing import Literal, overload
from ...core.entities.invocation import InvokeType
from ...core.runtime import BackwardsInvocation


class ChatAppInvocation(BackwardsInvocation[dict]):
    @overload
    def invoke(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming"],
        conversation_id: str,
        files: list,
    ) -> Generator[dict, None, None]: ...

    @overload
    def invoke(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["blocking"],
        conversation_id: str,
        files: list,
    ) -> dict: ...

    def invoke(
        self,
        app_id: str,
        inputs: dict,
        response_mode: Literal["streaming", "blocking"],
        conversation_id: str,
        files: list,
    ) -> Generator[dict, None, None] | dict:
        """
        Invoke chat app
        """
        response = self._backwards_invoke(
            InvokeType.App,
            dict,
            {
                "app_id": app_id,
                "inputs": inputs,
                "response_mode": response_mode,
                "conversation_id": conversation_id,
                "files": files,
            },
        )

        if response_mode == "streaming":
            return response

        for data in response:
            return data

        raise Exception("No response from chat")
