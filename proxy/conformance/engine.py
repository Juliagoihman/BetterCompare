from datetime import datetime

RULES = [
    {
        "id": "MISSING_NAME",
        "group": "schema",
        "severity": "ERROR",
        "check": lambda t: not t.get("name"),
        "reason": lambda t: "Tool has no name",
        "fix": "Add a 'name' field to the tool definition"
    },
    {
        "id": "MISSING_SCHEMA",
        "group": "schema",
        "severity": "ERROR",
        "check": lambda t: not t.get("input_schema"),
        "reason": lambda t: f"Tool '{t.get('name')}' has no input_schema",
        "fix": "Add an 'input_schema' with type, properties and required fields"
    },
    {
        "id": "MISSING_DESCRIPTION",
        "group": "schema",
        "severity": "WARNING",
        "check": lambda t: not t.get("description") or len(t.get("description", "")) < 10,
        "reason": lambda t: f"Tool '{t.get('name')}' has no meaningful description",
        "fix": "Add a description of at least 10 characters explaining what the tool does"
    },
    {
        "id": "ADMIN_TOOL",
        "group": "safety",
        "severity": "ERROR",
        "check": lambda t: any(
            word in t.get("name", "").lower()
            for word in ["admin", "debug", "internal", "test"]
        ),
        "reason": lambda t: f"Tool '{t.get('name')}' looks like an internal tool",
        "fix": "Remove or rename tools not meant for external use"
    },
    {
        "id": "NAMING_SNAKE_CASE",
        "group": "naming",
        "severity": "WARNING",
        "check": lambda t: t.get("name", "") != t.get("name", "").lower().replace("-", "_"),
        "reason": lambda t: f"Tool '{t.get('name')}' should use snake_case",
        "fix": "Rename tool to use lowercase and underscores only"
    },
    {
        "id": "MISSING_REQUIRED",
        "group": "ux",
        "severity": "WARNING",
        "check": lambda t: not t.get("input_schema", {}).get("required"),
        "reason": lambda t: f"Tool '{t.get('name')}' has no required fields defined",
        "fix": "Add a 'required' array listing mandatory parameters"
    },
]

def review_tool(tool: dict, vertical: str) -> dict:
    violations = []
    blocked = False

    for rule in RULES:
        if rule["check"](tool):
            violation = {
                "rule_id": rule["id"],
                "group": rule["group"],
                "severity": rule["severity"],
                "reason": rule["reason"](tool),
                "fix": rule["fix"]
            }
            violations.append(violation)
            if rule["severity"] == "ERROR":
                blocked = True

    # Compute score: start at 100, deduct per violation
    deductions = sum(
        30 if v["severity"] == "ERROR" else
        10 if v["severity"] == "WARNING" else 2
        for v in violations
    )
    score = max(0, 100 - deductions)

    # Determine status
    if blocked:
        status = "blocked"
    elif violations:
        status = "adapted"
    else:
        status = "accepted"

    return {
        "status": status,
        "score": score,
        "violations": violations,
        "checked_at": datetime.utcnow().isoformat()
    }
