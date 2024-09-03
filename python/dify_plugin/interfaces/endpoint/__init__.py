from abc import ABC, abstractmethod
from collections.abc import Mapping
from werkzeug import Request, Response

from dify_plugin.core.runtime import Session



class Endpoint(ABC):
    def __init__(self, session: Session) -> None:
        self.session = session

    def invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        return self._invoke(r, values, settings)

    @abstractmethod
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.

        To be implemented by subclasses.
        """
