import logging

from mcp.server.fastmcp import FastMCP

from x10.tools.mcp.private_tools import register_tools as register_private_tools
from x10.tools.mcp.public_tools import register_tools as register_public_tools

LOGGER = logging.getLogger()

mcp = FastMCP("Extended DEX MCP Server")

register_public_tools(mcp)
register_private_tools(mcp)

if __name__ == "__main__":
    # FIXME
    mcp.run(transport="streamable-http")
    # mcp.run()
