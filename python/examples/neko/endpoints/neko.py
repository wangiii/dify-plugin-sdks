import time
from typing import Mapping
from werkzeug import Request, Response
from dify_plugin import Endpoint

text = """<pre>
                   _____
                  /  __  \\
 / \\ ----/ \\     / /    \\ \\
                 \\/      \\ \\
  < >   < >              | |
\\     ^     /------------| |     <-- It's Yeuoly's cat! you can touch her if you want ~
  \\  -^-  /        ____    |       (but it's not recommended, she might bite, have a nice day!)
 |   ---          /    \\   |
 |                      |  |
  \\--  \\         /------|  /
   --------------_________/
</pre>
"""


class Neko(Endpoint):
    def _invoke(self, r: Request, values: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """

        def generator():
            try:
                visitors = int(self.session.storage.get("visitors").decode())
            except Exception:
                visitors = 0

            visitors += 1

            try:
                self.session.storage.set("visitors", str(visitors).encode())
            except Exception:
                pass

            yield f"it's your {visitors} time visit this page! <br>"

            for i in range(0, len(text), 2):
                time.sleep(0.05)
                yield text[i : i + 2]

        return Response(generator(), status=200, content_type="text/html")
