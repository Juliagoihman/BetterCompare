# proxy/main.py
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import httpx
import uuid
import os
import json
from datetime import datetime

from conformance.engine import review_tool, CURRENT_VERSION
from catalog.versions import get_version_manifest, VERTICAL_VERSIONS
from monitoring.tracer import tracer
from monitoring.stats import stats
from monitoring.session_store import session_store
from feedback.store import feedback_store

# ─── Vertical URLs ─────────────────────────────────────────────────────────────

VERTICALS = {
    "internet":  "http://127.0.0.1:8801/mcp",
    "mobile":    "http://127.0.0.1:8802/mcp",
    "travel":    "http://127.0.0.1:8803/mcp",
    "insurance": "http://127.0.0.1:8804/mcp",
}

# ─── Tool loading via real MCP client ─────────────────────────────────────────

async def _fetch_tools_from_vertical(vertical: str, url: str) -> list:
    tools = []
    try:
        async with streamable_http_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                for tool in result.tools:
                    raw = {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema or {}
                    }
                    report = review_tool(raw, vertical)
                    feedback_store.record(vertical, raw, report)
                    stats.record_tool(vertical, report["status"])
                    if report["status"] != "blocked":
                        tools.append({
                            "name": f"{vertical}__{tool.name}",
                            "description": tool.description or "",
                            "inputSchema": tool.inputSchema or {}
                        })
    except Exception as e:
        stats.record_error(vertical)
        print(f"[proxy] Could not connect to {vertical}: {e}")
    return tools

async def _load_all_tools(vertical_filter: str = None) -> list:
    all_tools = []
    targets = (
        {vertical_filter: VERTICALS[vertical_filter]}
        if vertical_filter and vertical_filter in VERTICALS
        else VERTICALS
    )
    for vertical, url in targets.items():
        tools = await _fetch_tools_from_vertical(vertical, url)
        all_tools.extend(tools)
    return all_tools

# ─── MCP Proxy Server ──────────────────────────────────────────────────────────

proxy = FastMCP(
    "bettercompare-proxy",
    instructions=(
        "BetterCompare aggregates CHECK24 comparison verticals: "
        "internet, mobile, travel, and insurance. "
        "Tools are namespaced as vertical__tool_name."
    )
)

_tool_registry: dict[str, dict] = {}

def _make_tool_handler(vertical: str, original_name: str):
    async def handler(**kwargs) -> str:
        qualified = f"{vertical}__{original_name}"
        correlation_id = str(uuid.uuid4())[:8]
        tracer.start(correlation_id, qualified, vertical)
        call_start = datetime.utcnow()
        try:
            async with streamable_http_client(VERTICALS[vertical]) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tracer.step(correlation_id, "vertical_call")
                    result = await session.call_tool(original_name, kwargs)
                    tracer.end(correlation_id, "ok")
                    stats.record_call(vertical, qualified)
                    latency_ms = round(
                        (datetime.utcnow() - call_start).total_seconds() * 1000
                    )
                    session_store.record("proxy", qualified, vertical, "ok", latency_ms)
                    for block in result.content:
                        if hasattr(block, "text"):
                            return block.text
                    return json.dumps({"status": "ok"})
        except Exception as e:
            tracer.end(correlation_id, "error", str(e))
            stats.record_error(vertical)
            return json.dumps({"error": str(e)})

    handler.__name__ = f"{vertical}__{original_name}"
    return handler

async def _register_dynamic_tools():
    all_tools = await _load_all_tools()
    for tool in all_tools:
        namespaced = tool["name"]
        vertical, original = namespaced.split("__", 1)
        handler = _make_tool_handler(vertical, original)
        proxy.add_tool(
            handler,
            name=namespaced,
            description=tool.get("description", ""),
        )
        _tool_registry[namespaced] = {"vertical": vertical, "original_name": original}
    print(f"[proxy] Registered {len(all_tools)} tools")

# ─── FastAPI side-car ──────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.responses import JSONResponse

admin = FastAPI(title="BetterCompare Admin")

dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.isdir(dashboard_dir):
    admin.mount("/static", StaticFiles(directory=dashboard_dir), name="static")

@admin.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    path = os.path.join(dashboard_dir, "index.html")
    with open(path) as f:
        return f.read()

@admin.get("/health")
async def health():
    results = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in VERTICALS.items():
            try:
                await client.get(url.replace("/mcp", ""))
                results[name] = "ok"
            except:
                results[name] = "unreachable"
    return results

@admin.get("/catalog")
async def catalog():
    return feedback_store.get_catalog()

@admin.get("/feedback")
async def feedback(vertical: str = None):
    return feedback_store.get(vertical)

@admin.get("/traces")
async def traces():
    return tracer.get_all()

@admin.post("/traces/clear")
async def clear_traces():
    tracer.clear()
    return {"status": "cleared"}

@admin.get("/stats")
async def get_stats():
    return stats.get_all()

@admin.get("/sessions")
async def sessions(session_id: str = None):
    if session_id:
        s = session_store.get(session_id)
        return s or {"error": "Session not found"}
    return session_store.get_all()

@admin.post("/sessions/clear")
async def clear_sessions():
    session_store.clear()
    return {"status": "cleared"}

@admin.post("/feedback/clear")
async def clear_feedback():
    feedback_store.clear()
    return {"status": "cleared"}

@admin.post("/reload")
async def reload():
    _tool_registry.clear()
    await _register_dynamic_tools()
    return {"status": "reloaded", "tools": len(_tool_registry)}

@admin.get("/versions")
async def versions():
    from conformance.engine import VERSION_POLICY
    manifest = get_version_manifest()
    manifest["conformance_policy"] = {
        "current": CURRENT_VERSION,
        "policies": VERSION_POLICY
    }
    return manifest

@admin.get("/versions/check")
async def check_version(vertical: str):
    v = VERTICAL_VERSIONS.get(vertical)
    if not v:
        return {"error": f"Unknown vertical: {vertical}"}
    notes = {
        "stable": "Safe to use in production",
        "beta": "May change — not recommended for production",
        "deprecated": "Will be removed in next major version"
    }
    return {**v, "vertical": vertical, "notes": notes.get(v["status"])}

@admin.post("/validate")
async def validate_tool(request: Request):
    body = await request.json()
    tool = body.get("tool", {})
    vertical = body.get("vertical", "unknown")
    if not tool:
        return JSONResponse({"error": "No tool provided"}, status_code=400)
    report = review_tool(tool, vertical)
    return {
        "tool_name": tool.get("name", "unknown"),
        "vertical": vertical,
        **report,
        "summary": {
            "errors": len([v for v in report["violations"] if v["severity"] == "ERROR"]),
            "warnings": len([v for v in report["violations"] if v["severity"] == "WARNING"]),
            "passed": len(report["violations"]) == 0
        }
    }

# ─── Combined ASGI app ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    await _register_dynamic_tools()
    yield

from starlette.applications import Starlette
from starlette.routing import Mount

mcp_app = proxy.streamable_http_app()

combined = Starlette(
    routes=[
        Mount("/mcp", app=mcp_app),
        Mount("/", app=admin),
    ],
    lifespan=lifespan,
)

if __name__ == "__main__":
    uvicorn.run(combined, host="0.0.0.0", port=8787)
