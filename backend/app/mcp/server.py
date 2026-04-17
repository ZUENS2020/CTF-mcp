from __future__ import annotations

from fastmcp import FastMCP

from app.mcp.tools.bore import list_bore_tunnels, start_bore, stop_bore
from app.mcp.tools.callback import get_callbacks
from app.mcp.tools.shell import read_file, shell_exec, upload_file

mcp = FastMCP("ctf-autopwn")

mcp.tool()(shell_exec)
mcp.tool()(upload_file)
mcp.tool()(read_file)
mcp.tool()(start_bore)
mcp.tool()(stop_bore)
mcp.tool()(list_bore_tunnels)
mcp.tool()(get_callbacks)
