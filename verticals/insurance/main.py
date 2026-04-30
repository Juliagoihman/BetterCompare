from fastapi import FastAPI

app = FastAPI(title="Insurance MCP")

@app.get("/")
def home():
    return {"vertical": "insurance", "status": "running"}

@app.get("/tools")
def tools():
    return [
        {
            "name": "compare_insurance_plans",
            "description": "Compare insurance plans by coverage and price.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "insurance_type": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["insurance_type"]
            }
        },
        {
            "name": "get_insurance_quote",
            "description": "",
            "input_schema": {
                "type": "object",
                "properties": {
                    "insurance_type": {"type": "string"}
                },
                "required": ["insurance_type"]
            }
        },
        {
            "name": "admin_reset_quotes",
            "description": "Internal admin tool.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "confirm": {"type": "boolean"}
                },
                "required": ["confirm"]
            }
        }
    ]
