# cwd: examples/basic_math
# lib: dify-plugin
# import sys
import sys
sys.path.append('../..')

from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.plugin import Plugin

plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=30))

if __name__ == '__main__':
    plugin.run()
