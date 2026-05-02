from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from catalog.versions import get_version_manifest
from monitoring.session_store import session_store
from openai import OpenAI
import httpx
import uuid
import os
import json
import asyncio
from datetime import datetime

from conformance.engine import review_tool
from monitoring.tracer import tracer
from monitoring.stats import stats
from feedback.store import feedback_store

VERTICALS = {
    "internet":  "http://127.0.0.1:8801",
    "mobile":    "http://127.0.0.1:8802",
    "travel":    "http://127.0.0.1:8803",
    "insurance": "http://127.0.0.1:8804",
}

async def _load_tools():
    async with httpx.AsyncClient(timeout=5.0) as client:
        for vertical, url in VERTICALS.items():
            try:
                res = await client.get(f"{url}/tools")
                raw_tools = res.json()
                for tool in raw_tools:
                    report = review_tool(tool, vertical)
                    feedback_store.record(vertical, tool, report)
                    stats.record_tool(vertical, report["status"])
            except Exception as e:
                stats.record_error(vertical)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await _load_tools()
    yield

app = FastAPI(title="BetterCompare MCP Proxy", lifespan=lifespan)

app.mount("/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "dashboard")),
    name="static")

@app.post("/mcp")
async def mcp(request: Request):
    body = await request.json()
    method = body.get("method")
    req_id = body.get("id", 1)

    vertical_filter = (
        request.query_params.get("vertical") or
        request.headers.get("x-vertical")
    )

    accept = request.headers.get("accept", "")
    use_sse = "text/event-stream" in accept

    if method == "initialize":
        result = _initialize(req_id)
    elif method == "tools/list":
        result = await _tools_list(req_id, vertical_filter)
    elif method == "tools/call":
        result = await _tools_call(req_id, body.get("params", {}), dict(request.headers))
    else:
        result = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

    if use_sse:
        async def stream():
            yield f"data: {json.dumps(result)}\n\n"
        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    return JSONResponse(result)

def _initialize(req_id):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {
                "name": "bettercompare-mcp-proxy",
                "version": "1.0.0"
            }
        }
    }

async def _tools_list(req_id, vertical_filter=None):
    tools = []
    verticals = {vertical_filter: VERTICALS[vertical_filter]} \
                if vertical_filter and vertical_filter in VERTICALS \
                else VERTICALS

    async with httpx.AsyncClient(timeout=5.0) as client:
        for vertical, url in verticals.items():
            try:
                res = await client.get(f"{url}/tools")
                raw_tools = res.json()
                for tool in raw_tools:
                    report = review_tool(tool, vertical)
                    feedback_store.record(vertical, tool, report)
                    stats.record_tool(vertical, report["status"])
                    if report["status"] != "blocked":
                        tools.append({
                            "name": f"{vertical}__{tool['name']}",
                            "description": tool.get("description", ""),
                            "inputSchema": tool.get("input_schema", {})
                        })
            except Exception as e:
                stats.record_error(vertical)

    return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

async def _tools_call(req_id, params, headers={}):
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    if "__" not in tool_name:
        return _error(req_id, -32602, "Tool name must be namespaced: vertical__tool_name")

    vertical, original_name = tool_name.split("__", 1)
    url = VERTICALS.get(vertical)

    if not url:
        return _error(req_id, -32602, f"Unknown vertical: {vertical}")

    correlation_id = str(uuid.uuid4())[:8]
    tracer.start(correlation_id, tool_name, vertical)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tracer.step(correlation_id, "vertical_call")
            res = await client.post(
                f"{url}/tools/{original_name}/call",
                json={"arguments": arguments}
            )
            result = res.json()
            tracer.end(correlation_id, "ok")
            stats.record_call(vertical, tool_name)

            session_id = headers.get("x-session-id", "anonymous")
            session_store.record(session_id, tool_name, vertical, "ok")

            return {"jsonrpc": "2.0", "id": req_id, "result": result}

    except Exception as e:
        tracer.end(correlation_id, "error", str(e))
        stats.record_error(vertical)
        return _error(req_id, -32603, f"Vertical call failed: {str(e)}")

def _error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

@app.get("/health")
async def health():
    results = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in VERTICALS.items():
            try:
                await client.get(url)
                results[name] = "ok"
            except:
                results[name] = "unreachable"
    return results

@app.get("/catalog")
async def catalog():
    await _load_tools()
    return feedback_store.get_catalog()

@app.get("/feedback")
async def feedback(vertical: str = None):
    return feedback_store.get(vertical)

@app.get("/traces")
async def traces():
    return tracer.get_all()

@app.get("/stats")
async def get_stats():
    return stats.get_all()

@app.get("/sessions")
async def sessions(session_id: str = None):
    if session_id:
        s = session_store.get(session_id)
        if not s:
            return {"error": "Session not found"}
        return s
    return session_store.get_all()

@app.post("/reload")
async def reload():
    await _load_tools()
    return {"status": "reloaded", "message": "Tool catalog refreshed"}

@app.get("/versions")
async def versions():
    return get_version_manifest()

@app.get("/versions/check")
async def check_version(vertical: str):
    from catalog.versions import VERTICAL_VERSIONS
    v = VERTICAL_VERSIONS.get(vertical)
    if not v:
        return {"error": f"Unknown vertical: {vertical}"}
    return {
        "vertical": vertical,
        "version": v["version"],
        "status": v["status"],
        "notes": {
            "stable": "Safe to use in production",
            "beta": "May change — not recommended for production",
            "deprecated": "Will be removed in next major version"
        }.get(v["status"])
    }

@app.get("/openapi-schema")
async def openapi_schema():
    tools = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for vertical, url in VERTICALS.items():
            try:
                res = await client.get(f"{url}/tools")
                raw_tools = res.json()
                for tool in raw_tools:
                    report = review_tool(tool, vertical)
                    if report["status"] != "blocked":
                        tools.append((vertical, tool))
            except:
                pass

    paths = {}
    for vertical, tool in tools:
        name = f"{vertical}__{tool['name']}"
        schema = tool.get("input_schema", {})
        paths[f"/tools/{name}/call"] = {
            "post": {
                "operationId": name,
                "summary": tool.get("description", f"Call {name}"),
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": schema
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Tool result",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "BetterCompare MCP Proxy",
            "version": "1.0.0",
            "description": "Compare internet, mobile, travel and insurance offers"
        },
        "servers": [{"url": "https://bettercompare.dev"}],
        "paths": paths
    }

@app.post("/tools/{vertical}__{tool_name}/call")
async def call_tool(vertical: str, tool_name: str, request: Request):
    body = await request.json()

    url = VERTICALS.get(vertical)
    if not url:
        return JSONResponse({"error": f"Unknown vertical: {vertical}"}, status_code=404)

    qualified_name = f"{vertical}__{tool_name}"
    correlation_id = str(uuid.uuid4())[:8]
    tracer.start(correlation_id, qualified_name, vertical)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tracer.step(correlation_id, "vertical_call")
            res = await client.post(
                f"{url}/tools/{tool_name}/call",
                json={"arguments": body}
            )
            result = res.json()
            tracer.end(correlation_id, "ok")
            stats.record_call(vertical, qualified_name)
            session_store.record("chatgpt", qualified_name, vertical, "ok")
            return result
    except Exception as e:
        tracer.end(correlation_id, "error", str(e))
        stats.record_error(vertical)
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_message = body.get("message", "")

    if not user_message:
        return JSONResponse({"error": "No message provided"}, status_code=400)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return JSONResponse({"error": "OpenAI API key not configured"}, status_code=500)

    openai_client = OpenAI(api_key=api_key)

    # Get tools from verticals
    tools = []
    async with httpx.AsyncClient(timeout=5.0) as http:
        for vertical, url in VERTICALS.items():
            try:
                res = await http.get(f"{url}/tools")
                raw_tools = res.json()
                for tool in raw_tools:
                    report = review_tool(tool, vertical)
                    if report["status"] != "blocked":
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": f"{vertical}__{tool['name']}",
                                "description": tool.get("description", ""),
                                "parameters": tool.get("input_schema", {})
                            }
                        })
            except:
                pass

    # Call OpenAI with tools
    messages = [{"role": "user", "content": user_message}]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # If OpenAI wants to call a tool
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        vertical, original_name = tool_name.split("__", 1)
        url = VERTICALS.get(vertical)

        async with httpx.AsyncClient(timeout=10.0) as http:
            res = await http.post(
                f"{url}/tools/{original_name}/call",
                json={"arguments": arguments}
            )
            tool_result = res.json()

        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result)
        })

        final_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        return {
            "response": final_response.choices[0].message.content,
            "tool_used": tool_name,
            "tool_result": tool_result
        }

    return {"response": message.content, "tool_used": None}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    path = os.path.join(os.path.dirname(__file__), "dashboard/index.html")
    with open(path) as f:
        return f.read()
  
