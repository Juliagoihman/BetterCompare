from datetime import datetime

# Version manifest — update this when you ship changes
PROXY_VERSION = "1.0.0"
CATALOG_VERSION = "2026-04-30"

VERTICAL_VERSIONS = {
    "internet":  {"version": "1.2.0", "status": "stable"},
    "mobile":    {"version": "1.1.0", "status": "stable"},
    "travel":    {"version": "1.0.0", "status": "stable"},
    "insurance": {"version": "0.9.0", "status": "beta"},
}

def get_version_manifest():
    return {
        "proxy_version": PROXY_VERSION,
        "catalog_version": CATALOG_VERSION,
        "verticals": VERTICAL_VERSIONS,
        "generated_at": datetime.utcnow().isoformat()
    }

def detect_breaking_change(vertical: str, old_tool: dict, new_tool: dict) -> dict | None:
    old_required = set(old_tool.get("input_schema", {}).get("required", []))
    new_required = set(new_tool.get("input_schema", {}).get("required", []))

    # New required params = breaking change
    added_required = new_required - old_required
    if added_required:
        return {
            "type": "NEW_REQUIRED_PARAM",
            "severity": "BREAKING",
            "detail": f"New required parameters: {list(added_required)}",
            "impact": "Existing ChatGPT calls will fail — coordinate before deploying",
            "vertical": vertical,
            "tool": new_tool.get("name")
        }

    # Param type changed = breaking change
    old_props = old_tool.get("input_schema", {}).get("properties", {})
    new_props = new_tool.get("input_schema", {}).get("properties", {})
    for key, new_prop in new_props.items():
        old_prop = old_props.get(key)
        if old_prop and old_prop.get("type") != new_prop.get("type"):
            return {
                "type": "PARAM_TYPE_CHANGED",
                "severity": "BREAKING",
                "detail": f"'{key}' changed from {old_prop.get('type')} to {new_prop.get('type')}",
                "impact": "ChatGPT may pass wrong types — tool will error at runtime",
                "vertical": vertical,
                "tool": new_tool.get("name")
            }

    # Tool removed = breaking change
    return None
