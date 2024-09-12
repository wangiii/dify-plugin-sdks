import json
from typing import Mapping
from werkzeug import Request, Response
from dify_plugin import Endpoint


class Duck(Endpoint):
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        app_id = values["app_id"]

        def generator():
            response = self.session.app.workflow.invoke(
                app_id=app_id, inputs={}, response_mode="streaming", files=[]
            )

            for data in response:
                yield f"{json.dumps(data)} <br>"

        return Response(generator(), status=200, content_type="text/html")
