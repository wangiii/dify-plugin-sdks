from typing import Mapping
from werkzeug import Request, Response
from dify_plugin.endpoint.endpoint import Endpoint


class Duck(Endpoint):
    def _invoke(self, r: Request, values: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        return Response("quack", status=200)
