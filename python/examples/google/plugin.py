from dify_plugin.config.config import DifyPluginEnv
from dify_plugin.plugin import Plugin


plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=30))
