from __future__ import annotations

from typing import Any, Callable, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mcp.tools.bore import list_bore_tunnels, start_bore, stop_bore
from app.mcp.tools.callback import get_callbacks
from app.mcp.tools.shell import ToolError, read_file, shell_exec, upload_file

router = APIRouter(tags=["mcp"])


class MCPToolRequest(BaseModel):
    tool: str = Field(description="tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict)


TOOL_REGISTRY: dict[str, Callable[..., Dict[str, Any]]] = {
    "shell_exec": shell_exec,
    "upload_file": upload_file,
    "read_file": read_file,
    "start_bore": start_bore,
    "stop_bore": stop_bore,
    "list_bore_tunnels": list_bore_tunnels,
    "get_callbacks": get_callbacks,
}


@router.post("/mcp")
def invoke_tool(payload: MCPToolRequest) -> Dict[str, Any]:
    tool = TOOL_REGISTRY.get(payload.tool)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"unknown tool: {payload.tool}")

    try:
        result = tool(**payload.arguments)
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TypeError as exc:
        raise HTTPException(status_code=422, detail=f"invalid arguments: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"tool": payload.tool, "result": result}
