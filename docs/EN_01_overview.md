BetterCompare — System Overview

## What is BetterCompare?

BetterCompare is a proxy server that sits between ChatGPT and multiple independent backend services (called "verticals"). Each vertical owns its own tools and data. BetterCompare aggregates them all into a single endpoint that ChatGPT can connect to.

```
ChatGPT
   │
   ▼
bettercompare.dev/mcp   ← one single endpoint
   │
   ├── internet  (port 8801)
   ├── mobile    (port 8802)
   ├── travel    (port 8803)
   └── insurance (port 8804)
```

ChatGPT never talks to the verticals directly. It only talks to the proxy.

---

## Why does this exist?

CHECK24 has many independent comparison products. Each product team owns their own code and tools. But from the customer's perspective, it's one brand — one app, one website, one ChatGPT connector.

The proxy solves this tension: one entry point for ChatGPT, independent ownership for each vertical team.

---

## The 5 Core Components

### 1. The Proxy (`proxy/main.py`)
The central piece. It:
- Connects to each vertical MCP server at startup
- Fetches their tools via the MCP protocol
- Runs each tool through the conformance engine
- Registers approved tools under namespaced names (`internet__compare_internet_offers`)
- Routes tool calls from ChatGPT to the correct vertical
- Tracks every call with a correlation ID

### 2. The Conformance Engine (`proxy/conformance/engine.py`)
A rule-based validator. Before any tool reaches ChatGPT, it must pass a set of checks:
- Does it have a name?
- Does it have a description?
- Does it have an input schema?
- Is it safe to expose (no admin/debug tools)?
- Does it follow naming conventions?

Tools that fail are either **adapted** (warnings only) or **blocked** (errors). Vertical teams receive structured feedback with a `fix` field explaining exactly what to change.

### 3. Versioning (`proxy/catalog/versions.py`)
Every component has an explicit version:
- The proxy itself (`1.0.0`)
- Each vertical (`internet: 1.2.0`, `insurance: 0.9.0`)
- The tool catalog (date-stamped)

A breaking change detector monitors for:
- New required parameters (existing ChatGPT calls would break)
- Parameter type changes (wrong data would be sent)

When a breaking change is detected, the proxy flags it before it reaches ChatGPT.

### 4. Per-Vertical QA Mode
Vertical teams can test their tools in isolation through the same proxy path ChatGPT uses — without seeing every other vertical's tools.

This is done via a query parameter or header:
```
POST /mcp?vertical=internet
POST /mcp  +  x-vertical: internet
```

This approach was chosen over separate deployments because it requires zero infrastructure changes and works with the existing connector URL.

### 5. Monitoring (`proxy/monitoring/`)
Three components:
- **Tracer**: assigns a `correlation_id` to every tool call, tracks per-step latency
- **Stats**: aggregates call counts, error rates, and conformance status per vertical
- **Session Store**: tracks tool usage across a conversation — which verticals were used, in what order

All data is visible at the live dashboard: `bettercompare.dev/dashboard`

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| MCP Protocol | Python MCP SDK (`mcp[cli]`) |
| Transport | Streamable HTTP (MCP standard, March 2025) |
| Web Framework | FastAPI + Starlette |
| HTTP Client | httpx |
| Deployment | Docker on Railway |

---

## Live Endpoints

| URL | Description |
|-----|-------------|
| `bettercompare.dev/mcp` | MCP endpoint for ChatGPT |
| `bettercompare.dev/dashboard` | Live monitoring dashboard |
| `bettercompare.dev/health` | Vertical reachability check |
| `bettercompare.dev/catalog` | Full tool catalog |
| `bettercompare.dev/feedback` | Conformance feedback |
| `bettercompare.dev/traces` | Request traces |
| `bettercompare.dev/sessions` | Session-level tool usage |
| `bettercompare.dev/versions` | Version manifest |
