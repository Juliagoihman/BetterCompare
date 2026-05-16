# BetterCompare — Versioning

## Why versioning matters

A ChatGPT app that gets approved by OpenAI is registered at a specific point in time. Any changes to tools, schemas, or behavior may require another review. Stability is not just a technical nicety — it is a product requirement.

BetterCompare treats versioning as a first-class concern: every component has an explicit version, breaking changes are detected automatically, and the proxy absorbs changes so ChatGPT remains stable.

---

## Version Manifest

Every component has its own version:

```json
{
  "proxy_version": "1.0.0",
  "catalog_version": "2026-04-30",
  "verticals": {
    "internet":  {"version": "1.2.0", "status": "stable"},
    "mobile":    {"version": "1.1.0", "status": "stable"},
    "travel":    {"version": "1.0.0", "status": "stable"},
    "insurance": {"version": "0.9.0", "status": "beta"}
  }
}
```

Available at: `GET /versions`

---

## Vertical Statuses

| Status | Meaning |
|--------|---------|
| `stable` | Safe to use, no breaking changes expected |
| `beta` | May change — not recommended for production |
| `deprecated` | Will be removed in the next major proxy version |

---

## Who does the work when something changes?

### Vertical team ships a non-breaking change
*(e.g. adds an optional parameter, improves a description)*

1. Vertical team updates their MCP server
2. Vertical team bumps their version in `catalog/versions.py` (minor or patch)
3. Proxy operator calls `POST /reload` to refresh the tool catalog
4. No ChatGPT review required — nothing visible to ChatGPT changed

### Vertical team ships a breaking change
*(e.g. adds a required parameter, changes a parameter type)*

1. Proxy's breaking change detector flags the change automatically
2. Vertical team receives a structured warning via `/feedback`
3. Vertical team and proxy operator coordinate — the change cannot go live until a migration path is agreed
4. Proxy operator bumps the **proxy major version** (`1.0.0` → `2.0.0`)
5. ChatGPT review may be required

### Proxy ships a new conformance rule
1. Proxy operator adds the rule to `conformance/engine.py`
2. All verticals are re-evaluated on next `POST /reload`
3. Newly blocked tools disappear from ChatGPT's tool list
4. Affected vertical teams receive feedback via `/feedback`

---

## Breaking Change Detection

The proxy automatically detects two types of breaking changes when tools are reloaded:

**New required parameter:**
```json
{
  "type": "NEW_REQUIRED_PARAM",
  "severity": "BREAKING",
  "detail": "New required parameters: ['zip_code']",
  "impact": "Existing ChatGPT calls will fail — coordinate before deploying"
}
```

**Parameter type changed:**
```json
{
  "type": "PARAM_TYPE_CHANGED",
  "severity": "BREAKING",
  "detail": "'min_speed' changed from string to integer",
  "impact": "ChatGPT may pass wrong types — tool will error at runtime"
}
```

---

## Check a specific vertical's version

```
GET /versions/check?vertical=insurance
```

```json
{
  "vertical": "insurance",
  "version": "0.9.0",
  "status": "beta",
  "notes": "May change — not recommended for production"
}
```
