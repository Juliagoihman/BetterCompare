from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

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
                    "include_phone": {"type": "boolean"}
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
                    "location": {"type": "string"},
                    "provider": {"type": "string"}
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
                    "brand": {"type": "string"},
                    "max_price": {"type": "number"}
                },
                "required": ["brand"]
            }
        }
    ]

class CallRequest(BaseModel):
    arguments: Dict[str, Any] = {}

@app.post("/tools/compare_mobile_plans/call")
def compare_mobile_plans(req: CallRequest):
    data_gb = req.arguments.get("data_gb", 5)
    return {
        "results": [
            {"provider": "Telekom", "data_gb": 15, "price": 19.99, "network": "5G"},
            {"provider": "O2", "data_gb": 10, "price": 14.99, "network": "4G"},
            {"provider": "Vodafone", "data_gb": 20, "price": 24.99, "network": "5G"}
        ],
        "min_data_gb": data_gb
    }

@app.post("/tools/get_best_mobile_deal/call")
def get_best_mobile_deal(req: CallRequest):
    data_gb = req.arguments.get("data_gb", 5)
    include_phone = req.arguments.get("include_phone", False)
    return {
        "best_deal": {"provider": "O2", "data_gb": 10, "price": 14.99, "network": "4G"},
        "include_phone": include_phone,
        "min_data_gb": data_gb
    }

@app.post("/tools/check_network_coverage/call")
def check_network_coverage(req: CallRequest):
    location = req.arguments.get("location", "unknown")
    return {
        "location": location,
        "coverage": {
            "Telekom": {"4G": True, "5G": True},
            "Vodafone": {"4G": True, "5G": False},
            "O2": {"4G": True, "5G": False}
        }
    }

@app.post("/tools/compare_phone_hardware/call")
def compare_phone_hardware(req: CallRequest):
    brand = req.arguments.get("brand", "Apple")
    return {
        "results": [
            {"model": f"{brand} Pro", "price": 999, "plan_included": "10GB Telekom"},
            {"model": f"{brand} Standard", "price": 799, "plan_included": "5GB O2"}
        ],
        "brand": brand
    }
