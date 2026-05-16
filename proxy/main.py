# proxy/main.py
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from starlette.applications import Starlette
from starlette.routing import Mount

from contextlib import asynccontextmanager
import uvicorn
import httpx
import uuid
import os
import json
from datetime import datetime
from openai import OpenAI

from proxy.conformance.engine import review_tool, CURRENT_VERSION
from proxy.catalog.versions import get_version_manifest, VERTICAL_VERSIONS
from proxy.monitoring.tracer import tracer
from proxy.monitoring.stats import stats
from proxy.monitoring.session_store import session_store
from proxy.feedback.store import feedback_store


VERTICALS = {
    "internet": "http://127.0.0.1:8801/mcp",
    "mobile": "http://127.0.0.1:8802/mcp",
    "travel": "http://127.0.0.1:8803/mcp",
    "insurance": "http://127.0.0.1:8804/mcp",
}


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
                        "input_schema": tool.inputSchema or {},
                    }

                    report = review_tool(raw, vertical)
                    feedback_store.record(vertical, raw, report)
                    stats.record_tool(vertical, report["status"])

                    if report["status"] != "blocked":
                        tools.append(
                            {
                                "name": f"{vertical}__{tool.name}",
                                "description": tool.description or "",
                                "inputSchema": tool.inputSchema or {},
                            }
                        )
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


async def _tools_call_internal(tool_name: str, arguments: dict):
    if "__" not in tool_name:
        return {"error": "Invalid tool name"}

    vertical, original_name = tool_name.split("__", 1)
    url = VERTICALS.get(vertical)

    if not url:
        return {"error": f"Unknown vertical: {vertical}"}

    correlation_id = str(uuid.uuid4())[:8]
    tracer.start(correlation_id, tool_name, vertical)
    call_start = datetime.utcnow()

    try:
        async with streamable_http_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tracer.step(correlation_id, "vertical_call")

                result = await session.call_tool(original_name, arguments)

                tracer.end(correlation_id, "ok")
                stats.record_call(vertical, tool_name)

                latency_ms = round(
                    (datetime.utcnow() - call_start).total_seconds() * 1000
                )
                session_store.record("ai-chat", tool_name, vertical, "ok", latency_ms)

                for block in result.content:
                    if hasattr(block, "text"):
                        try:
                            return json.loads(block.text)
                        except Exception:
                            return {"result": block.text}

                return {"status": "ok"}

    except Exception as e:
        tracer.end(correlation_id, "error", str(e))
        stats.record_error(vertical)
        return {"error": str(e)}


proxy = FastMCP(
    "bettercompare-proxy",
    instructions=(
        "BetterCompare aggregates CHECK24 comparison verticals: "
        "internet, mobile, travel, and insurance. "
        "Tools are namespaced as vertical__tool_name."
    ),
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

        if namespaced in _tool_registry:
            continue

        handler = _make_tool_handler(vertical, original)

        proxy.add_tool(
            handler,
            name=namespaced,
            description=tool.get("description", ""),
        )

        _tool_registry[namespaced] = {
            "vertical": vertical,
            "original_name": original,
        }

    print(f"[proxy] Registered {len(_tool_registry)} tools")


admin = FastAPI(title="BetterCompare Admin")

dashboard_dir = os.path.join(os.path.dirname(__file__), "dashboard")

if os.path.isdir(dashboard_dir):
    admin.mount("/static", StaticFiles(directory=dashboard_dir), name="static")


@admin.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    path = os.path.join(dashboard_dir, "index.html")
    with open(path, encoding="utf-8") as f:
        return f.read()


@admin.get("/health")
async def health():
    results = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in VERTICALS.items():
            try:
                await client.get(url.replace("/mcp", ""))
                results[name] = "ok"
            except Exception:
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
    from proxy.conformance.engine import VERSION_POLICY

    manifest = get_version_manifest()
    manifest["conformance_policy"] = {
        "current": CURRENT_VERSION,
        "policies": VERSION_POLICY,
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
        "deprecated": "Will be removed in next major version",
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
            "errors": len(
                [v for v in report["violations"] if v["severity"] == "ERROR"]
            ),
            "warnings": len(
                [v for v in report["violations"] if v["severity"] == "WARNING"]
            ),
            "passed": len(report["violations"]) == 0,
        },
    }


@admin.get("/openapi-schema")
async def openapi_schema():
    tools = await _load_all_tools()
    paths = {}

    for tool in tools:
        name = tool["name"]
        schema = tool.get("inputSchema", {})

        paths[f"/tools/{name}/call"] = {
            "post": {
                "operationId": name,
                "summary": tool.get("description", f"Call {name}"),
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": schema
                            if schema
                            else {"type": "object", "properties": {}}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Tool result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "result": {
                                            "type": "object",
                                            "description": "Tool execution result",
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
            }
        }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "BetterCompare MCP Proxy",
            "version": "1.0.0",
            "description": "Compare internet, mobile, travel and insurance offers",
        },
        "servers": [{"url": "https://bettercompare.dev"}],
        "paths": paths,
    }


@admin.post("/tools/{tool_path:path}/call")
async def call_tool_rest(tool_path: str, request: Request):
    body = await request.json()

    if "__" not in tool_path:
        return JSONResponse({"error": "Invalid tool path"}, status_code=400)

    vertical, original_name = tool_path.split("__", 1)
    url = VERTICALS.get(vertical)

    if not url:
        return JSONResponse(
            {"error": f"Unknown vertical: {vertical}"}, status_code=404
        )

    correlation_id = str(uuid.uuid4())[:8]
    tracer.start(correlation_id, tool_path, vertical)
    call_start = datetime.utcnow()

    try:
        async with streamable_http_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(original_name, body)

                tracer.end(correlation_id, "ok")
                stats.record_call(vertical, tool_path)

                latency_ms = round(
                    (datetime.utcnow() - call_start).total_seconds() * 1000
                )
                session_store.record("chatgpt", tool_path, vertical, "ok", latency_ms)

                for block in result.content:
                    if hasattr(block, "text"):
                        try:
                            return JSONResponse(json.loads(block.text))
                        except Exception:
                            return JSONResponse({"result": block.text})

                return JSONResponse({"status": "ok"})

    except Exception as e:
        tracer.end(correlation_id, "error", str(e))
        stats.record_error(vertical)
        return JSONResponse({"error": str(e)}, status_code=500)


@admin.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_message = body.get("message", "")
    history = body.get("history", [])

    if not user_message:
        return JSONResponse({"error": "No message provided"}, status_code=400)

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return JSONResponse(
            {"error": "OpenAI API key not configured"}, status_code=500
        )

    openai_client = OpenAI(api_key=api_key)
    all_tools = await _load_all_tools()

    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {}),
            },
        }
        for tool in all_tools
    ]

    messages = []

    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": user_message})

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=openai_tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        mcp_result = await _tools_call_internal(tool_name, arguments)

        messages.append(message)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(mcp_result),
            }
        )

        final_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )

        return {
            "response": final_response.choices[0].message.content,
            "tool_used": tool_name,
        }

    return {"response": message.content, "tool_used": None}

@asynccontextmanager
async def lifespan(app):
    try:
        await _register_dynamic_tools()
    except Exception as e:
        print("startup warning:", e)

    yield

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
