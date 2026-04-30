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
            "description": "Compare internet offers for a given address and minimum speed.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "Street address"},
                    "min_speed": {"type": "integer", "description": "Minimum speed in Mbit/s"}
                },
                "required": ["address"]
            }
        },
        {
            "name": "get_best_internet_deal",
            "description": "Get the single best internet deal for a given address.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "max_price": {"type": "number", "description": "Maximum monthly price in EUR"}
                },
                "required": ["address"]
            }
        },
        {
            "name": "check_availability",
            "description": "Check if internet service is available at a given address.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "provider": {"type": "string", "description": "Optional: specific provider name"}
                },
                "required": ["address"]
            }
        }
    ]
