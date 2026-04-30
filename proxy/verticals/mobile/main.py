from fastapi import FastAPI

app = FastAPI(title="Mobile MCP")

@app.get("/")
def home():
    return {"vertical": "mobile", "status": "running"}

@app.get("/tools")
def tools():
    return [
        {
            "name": "compare_mobile_plans",
            "description": "Compare mobile phone plans by data volume and price.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data_gb": {"type": "integer", "description": "Minimum data in GB"},
                    "max_price": {"type": "number", "description": "Maximum monthly price in EUR"}
                },
                "required": ["data_gb"]
            }
        },
        {
            "name": "get_best_mobile_deal",
            "description": "Get the best mobile plan for a given data requirement.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data_gb": {"type": "integer"},
                    "include_phone": {"type": "boolean", "description": "Include hardware deals"}
                },
                "required": ["data_gb"]
            }
        },
        {
            "name": "check_network_coverage",
            "description": "Check mobile network coverage for a specific location.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or address"},
                    "provider": {"type": "string", "description": "Network provider name"}
                },
                "required": ["location"]
            }
        },
        {
            "name": "compare_phone_hardware",
            "description": "Compare smartphone hardware deals with included plans.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "brand": {"type": "string", "description": "Phone brand e.g. Apple, Samsung"},
                    "max_price": {"type": "number"}
                },
                "required": ["brand"]
            }
        }
    ]
