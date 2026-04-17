from __future__ import annotations

from fastmcp import FastMCP

from app.mcp.tools.callback import get_callbacks
from app.mcp.tools.shell import read_file, shell_exec

mcp = FastMCP("ctf-autopwn")

mcp.tool()(shell_exec)
mcp.tool()(read_file)
mcp.tool()(get_callbacks)
