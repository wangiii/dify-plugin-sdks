from typing import Mapping
from werkzeug import Request, Response
from dify_plugin.webhook.webhook import Webhook


class Duck(Webhook):
    def _invoke(self, r: Request, values: Mapping) -> Response:
        """
        Invokes the webhook with the given request.
        """
        return Response("quack", status=200)
