from fastapi import FastAPI

app = FastAPI(title="Internet MCP")

@app.get("/")
def home():
    return {"vertical": "internet", "status": "running"}

@app.get("/tools")
def tools():
    return [
        {
            "name": "compare_internet_offers",
            "description": "Compare internet offers for a given address.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "min_speed": {"type": "integer"}
                },
                "required": ["address"]
            }
        }
    ]
