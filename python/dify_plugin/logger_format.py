import json
import logging


class DifyPluginLoggerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            'event': 'log',
            'data': {
                'level': record.levelname,
                'message': record.getMessage(),
                'timestamp': record.created,
            }
        })