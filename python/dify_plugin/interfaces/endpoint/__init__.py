from abc import ABC, abstractmethod
from collections.abc import Mapping
from werkzeug import Request, Response

from ...core.runtime import Session



class Endpoint(ABC):
    def __init__(self, session: Session) -> None:
        self.session = session

    ############################################################
    #        Methods that can be implemented by plugin         #
    ############################################################

    @abstractmethod
    def invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.

        To be implemented by subclasses.
        """

    ############################################################
    #                 For executor use only                    #
    ############################################################

    def invoke_from_executor(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        if type(self) is not Endpoint:
            raise RuntimeError("Subclasses cannot call this method.")

        return self.invoke(r, values, settings)