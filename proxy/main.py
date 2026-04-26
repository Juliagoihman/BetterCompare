from fastapi import FastAPI

app = FastAPI(title="BetterCompare Proxy")

# In der echten Version wären das separate MCP-Server.
# Für den Anfang simulieren wir sie direkt im Proxy.
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
        "message": "Proxy is running"
    }


@app.get("/tools")
def get_tools():
    aggregated_tools = []

    for vertical_name, tools in VERTICAL_TOOLS.items():
        for tool in tools:
            tool_with_vertical = tool.copy()
            tool_with_vertical["vertical"] = vertical_name
            aggregated_tools.append(tool_with_vertical)

    return aggregated_tools
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
