from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="Insurance MCP")

@app.get("/")
def home():
    return {"vertical": "insurance", "status": "running"}

@app.get("/tools")
def tools():
    return [
        {
            # Good tool - will be accepted
            "name": "compare_insurance_plans",
            "description": "Compare insurance plans by coverage and price.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "insurance_type": {"type": "string", "description": "Type of insurance"},
                    "age": {"type": "integer", "description": "Age of the insured person"}
                },
                "required": ["insurance_type"]
            }
        },
        {
            # Missing description - will be ADAPTED with WARNING
            "name": "get_insurance_quote",
            "description": "",
            "input_schema": {
                "type": "object",
                "properties": {
                    "insurance_type": {"type": "string"},
                    "coverage_amount": {"type": "number"}
                },
                "required": ["insurance_type"]
            }
        },
        {
            # Missing required field - will be ADAPTED with WARNING
            "name": "list_insurance_types",
            "description": "List all available insurance types.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"}
                }
            }
        },
        {
            # Admin tool - will be BLOCKED with ERROR
            "name": "admin_reset_quotes",
            "description": "Internal admin tool to reset all quotes.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "confirm": {"type": "boolean"}
                },
                "required": ["confirm"]
            }
        },
        {
            # Missing schema entirely - will be BLOCKED with ERROR
            "name": "debug_insurance_cache"
        }
    ]

class CallRequest(BaseModel):
    arguments: Dict[str, Any] = {}

@app.post("/tools/compare_insurance_plans/call")
def compare_insurance_plans(req: CallRequest):
    insurance_type = req.arguments.get("insurance_type", "health")
    return {
        "results": [
            {"provider": "Allianz", "coverage": "premium", "price": 89.99},
            {"provider": "AXA", "coverage": "basic", "price": 49.99},
            {"provider": "HanseMerkur", "coverage": "full", "price": 129.99}
        ],
        "insurance_type": insurance_type
    }

@app.post("/tools/get_insurance_quote/call")
def get_insurance_quote(req: CallRequest):
    return {
        "quote": 59.99,
        "provider": "Allianz",
        "valid_until": "2024-12-31"
    }

@app.post("/tools/list_insurance_types/call")
def list_insurance_types(req: CallRequest):
    return {
        "types": ["health", "car", "home", "travel", "life"]
    }
