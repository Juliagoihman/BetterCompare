# GenDev9 – CHECK24 ChatGPT App Challenge

## BetterCompare – Compare Everything in One Place

BetterCompare is a ChatGPT-native MCP proxy that aggregates multiple comparison services into a single unified interface.

---

# 1. 📘 Project Overview

**Project Name:** BetterCompare  
**Author:** Julia Goihman

Instead of exposing separate MCP connectors per vertical, this system provides:

* one **central ChatGPT-facing endpoint**
* intelligent **cross-vertical routing**
* strict **Apps SDK / MCP conformance filtering**
* transparent **feedback for vertical teams**

The system reflects a real CHECK24 challenge:

👉 Many independent products internally
👉 One seamless experience externally

Users can start with vague intents (e.g. *“I need cheap internet for students”*) and the proxy routes them to the correct vertical without requiring explicit product selection.

---

# 🚀 Live Demo

* **Proxy MCP Endpoint:** `<DEPLOYED_URL>`
* **MCP Inspector URL:** `<INSPECTOR_URL>`
* **(Optional) Monitoring Dashboard:** `<DASHBOARD_URL>`

> ⚠️ ChatGPT connects only to the proxy MCP. All vertical MCPs are hidden behind it.

---

# 📁 Repository Structure

```id="1s0gqg"
/proxy-mcp                 # ChatGPT-facing MCP (core system)
/verticals/
   /internet-mcp           # internet comparison vertical (based on BetterSurf logic)
   /mobile-mcp             # mock mobile plans vertical
   /travel-mcp             # mock travel / flights vertical
/shared/
   /schemas                # shared validation + tool schemas
   /routing                # intent detection + disambiguation logic
/docs                      # architecture + design decisions
```

---

# 2. ✅ Challenge Requirements

## ✅ Single ChatGPT-facing Proxy MCP

* Exactly **one MCP endpoint exposed**
* All verticals are **only accessible through the proxy**
* Proxy responsibilities:

  * tool aggregation
  * routing decisions
  * schema validation
  * safety filtering

---

## ✅ Vertical MCPs (Mocked)

Each vertical:

* runs as its **own MCP server**
* defines its **own tools independently**
* can evolve without breaking the proxy

### Implemented Verticals

| Vertical | Type      | Description                                                  |
| -------- | --------- | ------------------------------------------------------------ |
| Internet | Semi-real | Internet provider comparison (adapted from previous project) |
| Mobile   | Mock      | Mobile plan search and comparison                            |
| Travel   | Mock      | Flight / travel search                                       |

---

## ✅ ChatGPT-Conformant Tools

The proxy enforces:

* valid JSON schemas
* safe parameter structures
* clear, LLM-friendly tool descriptions

### Example Tool (Exposed via Proxy)

```json id="f5o6x6"
{
  "name": "compare_internet_providers",
  "description": "Compare internet providers for a given address",
  "input_schema": {
    "type": "object",
    "properties": {
      "address": { "type": "string" },
      "min_speed": { "type": "number" }
    },
    "required": ["address"]
  }
}
```

---

## ✅ Versioning Strategy

### Proxy Versioning

* Semantic versioning (`v1`, `v1.1`, `v2`)
* Changes affect:

  * tool exposure
  * routing logic
  * schema normalization

### Vertical Versioning

Each vertical exposes:

* version metadata
* supported capabilities

### Key Principle

👉 The proxy absorbs breaking changes so ChatGPT remains stable.

---

## ✅ Feedback to Vertical Teams

The proxy actively reports issues with tools:

* ❌ Non-conformant schemas
* ⚠️ Unsafe exposure
* 🔁 Required adaptations
* 🚫 Withheld tools

### Example Feedback

```json id="o9gxgg"
{
  "vertical": "travel",
  "tool": "searchFlight",
  "status": "rejected",
  "reason": "Ambiguous naming conflicts with another vertical",
  "suggestion": "Improve description or add intent metadata"
}
```

---

# 3. 🏗️ Architecture

## 🏛️ System Overview

```id="oeyyub"
ChatGPT
   │
   ▼
OmniCompare Proxy MCP
   ├── Routing Layer
   ├── Tool Registry
   ├── Conformance Validator
   ├── Feedback Engine
   │
   ├── Internet MCP
   ├── Mobile MCP
   └── Travel MCP
```

---

## 💻 Tech Stack

### Proxy MCP

* FastAPI (Python)
* Pydantic (schema validation)
* httpx (communication with vertical MCPs)
* Redis (optional caching & tracing)

### Vertical MCPs

* FastAPI microservices
* independent tool schemas
* mock or real logic

---

# 4. ⭐ Core Features

---

## 🔀 4.1 Cross-Vertical Routing

The proxy automatically determines which vertical should handle a request.

### Example

User:

> “I need cheap internet for students”

Routing:
→ Internet MCP

---

## ⚠️ 4.2 Tool Ambiguity Handling

Problem:
Different verticals may expose similarly named tools.

### Solution

* metadata tagging (intent categories)
* routing based on:

  * user query
  * conversation history
  * vertical context

👉 Best-effort disambiguation (not 100% solvable by design)

---

## 📡 4.3 Incremental / Streaming Responses

Inspired by the previous BetterSurf system:

* fast providers respond first
* slower providers follow
* results are streamed progressively

Benefits:

* faster perceived performance
* improved UX inside ChatGPT

---

## 🛡️ 4.4 Conformance Layer

Before exposing tools:

* schema validation
* input sanitization
* normalization of outputs

Ensures compatibility with ChatGPT Apps SDK expectations.

---

## 📊 4.5 Observability & Tracing

Each request includes:

* correlation ID
* latency per vertical
* error tracking

Example:

```id="c1p7xa"
trace_id=abc123
intent=internet
routed_to=internet-mcp
latency=420ms
```

---

## 🧪 4.6 Per-Vertical Testing Mode

Vertical teams can test their tools via the proxy in isolation.

### Example

```id="rd84ys"
X-Vertical-Test: internet
```

Result:

* only that vertical is exposed to ChatGPT
* enables realistic QA flows

---

# 5. 🔒 Security Considerations

* proxy acts as strict trust boundary
* no direct exposure of vertical MCPs
* schema-based input validation
* secrets remain server-side
* future: rate limiting & auth layer

---

# 6. ☁️ Deployment

### Proxy MCP

* publicly deployed at `<URL>`
* accessible by ChatGPT / MCP Inspector

### Vertical MCPs

* deployed internally
* not publicly accessible

---

# 7. 🧪 Testing

* unit tests for routing logic
* integration tests for proxy ↔ vertical interaction
* mock MCP servers for deterministic testing

---

# 8. ✨ Optional Features

### Implemented

* cross-vertical routing system
* ambiguity handling via metadata
* structured feedback system
* per-vertical testing mode

### Potential Extensions

* LLM-assisted routing improvements
* tool ranking system
* advanced monitoring dashboard

---

# 9. 🔮 Future Improvements

* smarter intent detection using embeddings
* automatic schema adaptation layer
* persistent analytics for conversations
* improved ambiguity resolution

---

# 10. 🎥 Video

📺 **Demo Video:** `<VIDEO_LINK>`

Includes:

* architecture explanation
* routing demo
* proxy + vertical interaction
* key design decisions

---

# 11. 🧠 Key Design Decisions

### Proxy as Gatekeeper

All tools must pass through validation and filtering before exposure.

### Vertical Independence

Each vertical remains fully decoupled and independently maintainable.

### Stability over Flexibility

The proxy protects ChatGPT from breaking changes in vertical MCPs.

---

# 12. 🚧 Known Limitations

* ambiguity between similar tools cannot be fully eliminated
* routing is heuristic-based (not perfect)
* mock verticals do not reflect full production complexity

---

# ❤️ Final Notes

OmniCompare MCP demonstrates how a **multi-product platform like CHECK24** can integrate seamlessly into ChatGPT using a **single, well-structured MCP proxy**.

The architecture is designed for:

* scalability
* maintainability
* future extensibility to other MCP-compatible hosts

---

**Made with ❤️ by Julia Goihman**
