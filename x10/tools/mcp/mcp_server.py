import logging

from mcp.server.fastmcp import FastMCP

from x10.core.env_config import EnvConfig
from x10.tools.mcp.private_tools import register_tools as register_private_tools
from x10.tools.mcp.public_tools import register_tools as register_public_tools

LOGGER = logging.getLogger()

mcp = FastMCP("Extended DEX MCP Server")

register_public_tools(mcp)
register_private_tools(mcp)


def log_config_info():
    env_config = EnvConfig.parse()
    LOGGER.info(
        "Starting MCP server with config: %s (API key set=%s, private key set=%s)",
        env_config.client_config_name,
        bool(env_config.api_key),
        bool(env_config.private_key),
    )


def start_http_server():
    log_config_info()
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    log_config_info()
    mcp.run(transport="stdio")
