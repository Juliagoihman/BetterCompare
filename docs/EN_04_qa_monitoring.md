# BetterCompare — Per-Vertical QA & Monitoring

## Per-Vertical QA Mode

### The problem

In a real deployment, multiple vertical teams work independently. When a team wants to test their tools end-to-end through ChatGPT, they face a problem: ChatGPT connects to one proxy URL, which returns all 14 tools from all 4 verticals. The team sees their 3 tools mixed in with everyone else's.

### The solution

The proxy supports a scoped view — it filters the tool catalog to only one vertical's tools, while keeping the same connector URL.

**Via query parameter:**
```
POST https://bettercompare.dev/mcp?vertical=internet
```

**Via header:**
```
POST https://bettercompare.dev/mcp
x-vertical: internet
```

When either is set, only that vertical's tools are returned in `tools/list` and only that vertical's tools can be called.

### Why this approach?

Three alternatives were considered:

| Option | Trade-off |
|--------|-----------|
| Separate deployment per vertical | Requires infrastructure changes, separate URLs |
| Separate proxy instance per vertical | Same problem — plus coordination overhead |
| Query param / header on existing proxy | Zero infrastructure changes, same connector URL, works today |

The query param / header approach was chosen because it requires no changes to ChatGPT's connector configuration and can be enabled or disabled per request.

### Limitation

If a vertical team has a ChatGPT Plus account, they can test with `?vertical=internet` in the connector URL. In developer/connector mode, the QA scope can be set via the header.

---

## Monitoring

### Tracing

Every tool call gets a unique `correlation_id`. The tracer records:
- Which tool was called
- Which vertical handled it
- How long each step took (conformance check, vertical call)
- Whether it succeeded or failed

```json
{
  "correlation_id": "a3f9b2c1",
  "tool_name": "internet__compare_internet_offers",
  "vertical": "internet",
  "total_ms": 142,
  "steps": [
    {"name": "vertical_call", "at_ms": 11}
  ],
  "status": "ok"
}
```

Available at: `GET /traces`

---

### Stats

Aggregated metrics per vertical:

```json
{
  "total_calls": 24,
  "total_errors": 0,
  "success_rate_pct": 100.0,
  "verticals": {
    "internet": {
      "calls": 8,
      "errors": 0,
      "error_rate_pct": 0.0
    }
  }
}
```

Available at: `GET /stats`

---

### Sessions

Tool usage tracked across a conversation:

```json
{
  "session_id": "sess_abc123",
  "flow": "internet__compare_internet_offers → travel__search_flights",
  "total_calls": 2,
  "verticals_used": ["internet", "travel"],
  "avg_latency_ms": 134
}
```

Available at: `GET /sessions`

The session ID comes from the `mcp-session-id` header that ChatGPT sends with every request — this is the standard way to correlate requests within one conversation.

---

### Dashboard

All of the above is visible in the live dashboard:

```
https://bettercompare.dev/dashboard
```

The dashboard shows:
- Total tools and conformance score
- Vertical health (green / amber / red)
- Conformance violations with fix suggestions
- Live trace timeline
- Session flows
- Top tools by usage
