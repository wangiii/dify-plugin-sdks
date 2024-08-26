from abc import ABC, abstractmethod
from collections.abc import Mapping
from werkzeug import Request, Response


class Endpoint(ABC):
    def invoke(self, r: Request, values: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        return self._invoke(r, values)

    @abstractmethod
    def _invoke(self, r: Request, values: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.

        To be implemented by subclasses.
        """
