from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
import httpx
import uuid
import os
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

@app.post("/mcp")
async def mcp(request: Request):
    body = await request.json()
    method = body.get("method")
    req_id = body.get("id", 1)
    vertical_filter = request.query_params.get("vertical")

    if method == "initialize":
        return _initialize(req_id)
    elif method == "tools/list":
        return await _tools_list(req_id, vertical_filter)
    elif method == "tools/call":
        return await _tools_call(req_id, body.get("params", {}))

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    })

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

async def _tools_call(req_id, params):
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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    path = os.path.join(os.path.dirname(__file__), "dashboard/index.html")
    with open(path) as f:
        return f.read()
  
