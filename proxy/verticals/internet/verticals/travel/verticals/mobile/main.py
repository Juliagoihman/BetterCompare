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
            "description": "Compare mobile phone plans.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data_gb": {"type": "integer"},
                    "max_price": {"type": "integer"}
                },
                "required": ["data_gb"]
            }
        }
    ]
