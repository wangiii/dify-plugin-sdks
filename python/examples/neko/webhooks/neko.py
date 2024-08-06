import time
from typing import Mapping
from werkzeug import Request, Response
from dify_plugin.webhook.webhook import Webhook

text = """/\__/\
      (  ・ω・)
      ( つ🌈つ
╔═══━━━━━━━━━━━━═══╗
║°°°°°°°°°°°°°°°°°°°°║
║°°°°°°°°°°°°°°°°°°°°║
║°°°°°°°°°°°°°°°°°°°°║
║°°°°°°°°°°°°°°°°°°°°║
║°°°°°°°°°°°°°°°°°°°°║
╚═══━━━━━━━━━━━━═══╝
   ∪∪             ∪∪
   
  ～～～～～～～～～～～～～～～～～～～～～～🌟"""

class Neko(Webhook):
    def _invoke(self, r: Request, values: Mapping) -> Response:
        """
        Invokes the webhook with the given request.
        """
        def generator():
            for i in range(0, len(text), 2):
                time.sleep(0.05)
                yield text[i:i+2]
        
        return Response(generator(), status=200, content_type="text/event-stream")