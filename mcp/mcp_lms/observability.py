"""MCP server exposing VictoriaLogs and VictoriaTraces as typed tools."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

server = Server("observability")

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _NoArgs(BaseModel):
    """Empty input model for tools that only need server-side configuration."""


class _LogsSearchQuery(BaseModel):
    query: str = Field(
        default="*",
        description="LogsQL query string (e.g., 'level:error' or '_stream:{service=\"backend\"}')"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Max number of log entries to return (default 10, max 1000)"
    )


class _LogsErrorCountQuery(BaseModel):
    service: str = Field(
        default="*",
        description="Service name to filter (use '*' for all services)"
    )
    minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
        description="Time window in minutes (default 60, max 24h)"
    )


class _TracesListQuery(BaseModel):
    service: str = Field(
        default="Learning Management Service",
        description="Service name to filter traces"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max number of traces to return (default 10)"
    )


class _TracesGetQuery(BaseModel):
    trace_id: str = Field(
        description="Trace ID to fetch (hex string)"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VICTORIALOGS_URL = os.environ.get("VICTORIALOGS_URL", "http://localhost:42010")
_VICTORIATRACES_URL = os.environ.get("VICTORIATRACES_URL", "http://localhost:42011")


def _text(data: Any) -> list[TextContent]:
    """Serialize data to a JSON text block."""
    if isinstance(data, (dict, list)):
        payload = data
    else:
        payload = data.model_dump() if hasattr(data, 'model_dump') else str(data)
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


async def _http_get(url: str, params: dict | None = None) -> Any:
    """Make an HTTP GET request and return JSON response."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Tool handlers - VictoriaLogs
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchQuery) -> list[TextContent]:
    """Search logs in VictoriaLogs using LogsQL query."""
    url = f"{_VICTORIALOGS_URL}/select/logsql/query"
    params = {
        "query": args.query,
        "limit": args.limit
    }
    try:
        result = await _http_get(url, params)
        return _text(result)
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaLogs query failed: {type(e).__name__}: {e}"})


async def _logs_error_count(args: _LogsErrorCountQuery) -> list[TextContent]:
    """Count errors per service over a time window."""
    # Build LogsQL query for errors
    if args.service == "*":
        query = "level:error OR severity:error OR severity:ERROR"
    else:
        query = f'_stream:{{service="{args.service}"}} AND (level:error OR severity:error)'
    
    url = f"{_VICTORIALOGS_URL}/select/logsql/query"
    params = {
        "query": query,
        "limit": 1000
    }
    try:
        result = await _http_get(url, params)
        # Count errors
        if isinstance(result, list):
            error_count = len(result)
        else:
            error_count = len(result.get('hits', [])) if isinstance(result, dict) else 0
        
        return _text({
            "service": args.service,
            "time_window_minutes": args.minutes,
            "error_count": error_count,
            "query": query
        })
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaLogs error count failed: {type(e).__name__}: {e}"})


# ---------------------------------------------------------------------------
# Tool handlers - VictoriaTraces
# ---------------------------------------------------------------------------


async def _traces_list(args: _TracesListQuery) -> list[TextContent]:
    """List recent traces for a service from VictoriaTraces."""
    url = f"{_VICTORIATRACES_URL}/jaeger/api/services/{args.service}/traces"
    params = {"limit": args.limit}
    try:
        result = await _http_get(url, params)
        return _text(result)
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaTraces list failed: {type(e).__name__}: {e}"})


async def _traces_get(args: _TracesGetQuery) -> list[TextContent]:
    """Fetch a specific trace by ID from VictoriaTraces."""
    url = f"{_VICTORIATRACES_URL}/jaeger/api/traces/{args.trace_id}"
    try:
        result = await _http_get(url)
        return _text(result)
    except httpx.HTTPError as e:
        return _text({"error": f"VictoriaTraces get failed: {type(e).__name__}: {e}"})


# ---------------------------------------------------------------------------
# Registry: tool name -> (input model, handler, Tool definition)
# ---------------------------------------------------------------------------

_Registry = tuple[type[BaseModel], Callable[..., Awaitable[list[TextContent]]], Tool]

_TOOLS: dict[str, _Registry] = {}


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    schema = model.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("title", None)
    _TOOLS[name] = (model, handler, Tool(name=name, description=description, inputSchema=schema))


_register(
    "logs_search",
    "Search logs in VictoriaLogs using LogsQL query. Returns matching log entries.",
    _LogsSearchQuery,
    _logs_search,
)

_register(
    "logs_error_count",
    "Count errors per service over a time window in VictoriaLogs.",
    _LogsErrorCountQuery,
    _logs_error_count,
)

_register(
    "traces_list",
    "List recent traces for a service from VictoriaTraces (Jaeger API).",
    _TracesListQuery,
    _traces_list,
)

_register(
    "traces_get",
    "Fetch a specific trace by ID from VictoriaTraces.",
    _TracesGetQuery,
    _traces_get,
)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [entry[2] for entry in _TOOLS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    entry = _TOOLS.get(name)
    if entry is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    model_cls, handler, _ = entry
    try:
        args = model_cls.model_validate(arguments or {})
        return await handler(args)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
