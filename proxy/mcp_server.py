from mcp.server.fastmcp import FastMCP
import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from main import proxy

if __name__ == "__main__":
    app = proxy.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8788)
