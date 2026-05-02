import httpx
import json
import os
from openai import OpenAI

PROXY_URL = "https://bettercompare.dev/mcp"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def fetch_mcp_tools():
    async with httpx.AsyncClient(timeout=10.0) as http:
        res = await http.post(PROXY_URL, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        })
        data = res.json()
        return data.get("result", {}).get("tools", [])

async def call_mcp_tool(name: str, arguments: dict):
    async with httpx.AsyncClient(timeout=10.0) as http:
        res = await http.post(PROXY_URL, json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments}
        })
        data = res.json()
        return data.get("result", {})
