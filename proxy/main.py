from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="BetterCompare Proxy")

VERTICAL_TOOLS = {
    "internet": [
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
    ],
    "travel": [
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
    ],
    "mobile": [
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
}


@app.get("/")
def home():
    return {
        "name": "BetterCompare",
        "message": "Proxy is running",
        "available_endpoints": [
            "/tools",
            "/tools?vertical=internet",
            "/route?query=Ich brauche schnelles Internet",
            "/feedback",
            "/version"
        ]
    }


@app.get("/tools")
def get_tools(vertical: str | None = Query(default=None)):
    aggregated_tools = []

    for vertical_name, tools in VERTICAL_TOOLS.items():
        if vertical and vertical != vertical_name:
            continue

        for tool in tools:
            tool_with_vertical = tool.copy()
            tool_with_vertical["vertical"] = vertical_name
            aggregated_tools.append(tool_with_vertical)

    return {
        "mode": "full" if vertical is None else "vertical-test",
        "selected_vertical": vertical,
        "tools": aggregated_tools
    }


@app.get("/route")
def route_request(query: str):
    query_lower = query.lower()

    if "internet" in query_lower or "wlan" in query_lower or "dsl" in query_lower:
        return {
            "query": query,
            "selected_vertical": "internet",
            "reason": "The query looks like an internet provider request."
        }

    if "reise" in query_lower or "flug" in query_lower or "hotel" in query_lower or "urlaub" in query_lower:
        return {
            "query": query,
            "selected_vertical": "travel",
            "reason": "The query looks like a travel request."
        }

    if "handy" in query_lower or "mobile" in query_lower or "sim" in query_lower:
        return {
            "query": query,
            "selected_vertical": "mobile",
            "reason": "The query looks like a mobile plan request."
        }

    return {
        "query": query,
        "selected_vertical": "unknown",
        "reason": "No clear vertical could be selected."
    }


@app.get("/feedback")
def get_feedback():
    feedback = []

    for vertical_name, tools in VERTICAL_TOOLS.items():
        for tool in tools:
            if "name" not in tool:
                feedback.append({
                    "vertical": vertical_name,
                    "status": "rejected",
                    "reason": "Tool is missing a name.",
                    "suggestion": "Add a unique tool name."
                })

            elif "description" not in tool:
                feedback.append({
                    "vertical": vertical_name,
                    "tool": tool.get("name"),
                    "status": "needs_adaptation",
                    "reason": "Tool is missing a description.",
                    "suggestion": "Add a clear description so ChatGPT can understand when to use it."
                })

            elif "input_schema" not in tool:
                feedback.append({
                    "vertical": vertical_name,
                    "tool": tool.get("name"),
                    "status": "rejected",
                    "reason": "Tool is missing an input_schema.",
                    "suggestion": "Add a valid JSON schema for tool inputs."
                })

            else:
                feedback.append({
                    "vertical": vertical_name,
                    "tool": tool.get("name"),
                    "status": "accepted",
                    "reason": "Tool passes basic conformance checks."
                })

    return feedback


@app.get("/version")
def get_version():
    return {
        "proxy": {
            "name": "BetterCompare Proxy",
            "version": "1.0.0",
            "policy": "The proxy keeps the ChatGPT-facing interface stable. Vertical changes are validated before exposure."
        },
        "verticals": {
            "internet": {
                "version": "1.0.0",
                "status": "compatible"
            },
            "travel": {
                "version": "1.0.0",
                "status": "compatible"
            },
            "mobile": {
                "version": "1.0.0",
                "status": "compatible"
            }
        }
    }
from pydantic import BaseModel
from typing import Dict, Any


class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


@app.post("/execute")
def execute_tool(request: ToolExecutionRequest):
    if request.tool_name == "compare_internet_offers":
        return {
            "tool": request.tool_name,
            "vertical": "internet",
            "result": [
                {
                    "provider": "SpeedyNet",
                    "price_per_month": "29.99€",
                    "speed": "250 Mbit/s"
                },
                {
                    "provider": "FiberFox",
                    "price_per_month": "34.99€",
                    "speed": "500 Mbit/s"
                }
            ]
        }

    if request.tool_name == "search_travel_offers":
        return {
            "tool": request.tool_name,
            "vertical": "travel",
            "result": [
                {
                    "destination": request.arguments.get("destination", "Mallorca"),
                    "price": "499€",
                    "type": "package holiday"
                }
            ]
        }

    if request.tool_name == "compare_mobile_plans":
        return {
            "tool": request.tool_name,
            "vertical": "mobile",
            "result": [
                {
                    "provider": "MobileMax",
                    "data": "20 GB",
                    "price_per_month": "14.99€"
                }
            ]
        }

    return {
        "error": "Unknown tool",
        "tool": request.tool_name
    }
