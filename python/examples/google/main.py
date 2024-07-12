# cwd: examples/basic_math
# lib: dify-plugin
# import sys
import sys
sys.path.append('../..')

from plugin import plugin

from provider.google import GoogleProvider

if __name__ == '__main__':
    plugin.run()
