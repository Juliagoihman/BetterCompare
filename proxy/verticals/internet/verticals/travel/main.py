from fastapi import FastAPI

app = FastAPI(title="Travel MCP")

@app.get("/")
def home():
    return {"vertical": "travel", "status": "running"}

@app.get("/tools")
def tools():
    return [
        {
            "name": "search_travel_offers",
            "description": "Search travel and vacation offers.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "budget": {"type": "integer"}
                },
                "required": ["destination"]
            }
        }
    ]
