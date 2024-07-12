# cwd: examples/basic_math
# lib: dify-plugin
# import sys
from collections.abc import Generator
import sys
import time
sys.path.append('../..')

from dify_plugin.config.config import DifyPluginConfig
from dify_plugin.core.runtime.entities.tool import ToolInvokeMessage
from dify_plugin import ToolProvider, Plugin
from dify_plugin.tool.entities import ToolProviderConfiguration
from dify_plugin.tool.tool import Tool
from dify_plugin.tool.entities import ToolConfiguration

plugin = Plugin(DifyPluginConfig(MAX_REQUEST_TIMEOUT=30))

@plugin.register_tool_provider
class BasicMath(ToolProvider):
    @classmethod
    def configuration(cls) -> ToolProviderConfiguration:
        return ToolProviderConfiguration(name='basic_math')

@plugin.register_tool(BasicMath)
class Add(Tool):
    @classmethod
    def configuration(cls) -> ToolConfiguration:
        return ToolConfiguration(name='add')
    
    def _invoke(self, user_id: str, tool_parameter: dict) -> Generator[ToolInvokeMessage, None]:
        result = tool_parameter['a'] + tool_parameter['b']
        yield self.create_text_message(f'The result is {result}')

if __name__ == '__main__':
    plugin.run()
