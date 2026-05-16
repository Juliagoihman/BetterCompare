# BetterCompare — Conformance Engine

## What is the Conformance Engine?

The conformance engine is a gatekeeper. Before any tool from a vertical MCP server reaches ChatGPT, it must pass a set of structured rules. Tools that fail are either adapted (with a warning) or blocked entirely.

This protects ChatGPT from receiving broken, unsafe, or confusing tools — and gives vertical teams clear, actionable feedback on what to fix.

---

## How it works

When the proxy starts up, it connects to each vertical and fetches their tools. For every tool, it runs through the rule list:

```
Tool from vertical
      │
      ▼
┌─────────────────┐
│  Rule: MISSING_NAME?        → ERROR  → blocked
│  Rule: MISSING_SCHEMA?      → ERROR  → blocked
│  Rule: MISSING_DESCRIPTION? → WARNING → adapted
│  Rule: ADMIN_TOOL?          → ERROR  → blocked
│  Rule: NAMING_SNAKE_CASE?   → WARNING → adapted
│  Rule: MISSING_REQUIRED?    → WARNING → adapted
└─────────────────┘
      │
      ▼
status: accepted / adapted / blocked
```

---

## The Rules

| Rule ID | Group | Severity | What it checks |
|---------|-------|----------|----------------|
| `MISSING_NAME` | schema | ERROR | Tool must have a name |
| `MISSING_SCHEMA` | schema | ERROR | Tool must have an input schema |
| `MISSING_DESCRIPTION` | schema | WARNING | Description must be at least 10 characters |
| `ADMIN_TOOL` | safety | ERROR | Names like "admin", "debug", "internal", "test" are blocked |
| `NAMING_SNAKE_CASE` | naming | WARNING | Tool name must use lowercase and underscores |
| `MISSING_REQUIRED` | ux | WARNING | Input schema must declare required fields |

---

## Tool Statuses

- **accepted** — tool passed all rules, exposed as-is
- **adapted** — tool has warnings but is still exposed (policy v1)
- **blocked** — tool has errors, not exposed to ChatGPT

---

## Policy Versions

The conformance engine supports two policy modes:

| Policy | Behavior |
|--------|----------|
| `v1` (default) | Lenient — tools with warnings are adapted and exposed |
| `v2` | Strict — tools with any violations are blocked |

Vertical teams can test against v2 before it becomes the default:
```
POST /mcp?version=v2
```

---

## Conformance Score

Each tool gets a score from 0–100:
- Every ERROR deducts 30 points
- Every WARNING deducts 10 points

The overall vertical score is the average across all its tools.

---

## Feedback for Vertical Teams

Every violation produces a structured feedback entry:

```json
{
  "rule_id": "MISSING_DESCRIPTION",
  "group": "schema",
  "severity": "WARNING",
  "reason": "Tool 'get_insurance_quote' has no meaningful description",
  "fix": "Add a description of at least 10 characters explaining what the tool does"
}
```

Teams can check their feedback at any time:
```
GET /feedback?vertical=insurance
```

The `fix` field is the key feature — teams know exactly what to change, not just that something is wrong.

---

## Validate a Tool Without Deploying

Teams can test a tool definition before deploying their vertical:

```bash
curl -X POST https://bettercompare.dev/validate \
  -H "Content-Type: application/json" \
  -d '{
    "vertical": "insurance",
    "tool": {
      "name": "get_quote",
      "description": "Get a quote",
      "input_schema": {
        "type": "object",
        "properties": {
          "age": {"type": "integer"}
        },
        "required": ["age"]
      }
    }
  }'
```
