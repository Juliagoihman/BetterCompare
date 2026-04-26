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
