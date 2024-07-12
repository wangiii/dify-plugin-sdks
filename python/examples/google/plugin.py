from dify_plugin.config.config import DifyPluginConfig
from dify_plugin.plugin import Plugin


plugin = Plugin(DifyPluginConfig(MAX_REQUEST_TIMEOUT=30))
