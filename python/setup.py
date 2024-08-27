from setuptools import setup

setup(
    name="dify_plugin",
    version="0.0.1-beta",
    author="langgenius",
    long_description_content_type="text/markdown",
    url="https://github.com/langgenius/dify-plugin-sdks.git",
    long_description=open("README.md", encoding="utf-8").read(),
    packages=["dify_plugin"],
    keywords=["dify", "plugin", "sdk"],
    requires=[
        "pydantic~=2.8.2",
        "pydantic_settings~=2.3.4",
        "pyyaml~=6.0.1",
        "transformers~=4.42.4",
        "Flask~=3.0.3",
        "gevent~=24.2.1",
        "Werkzeug~=3.0.3",
        "dpkt~=1.9.8",
        "awslambdaric~=2.1.0",
        "yarl~=1.9.4",
    ],
)
