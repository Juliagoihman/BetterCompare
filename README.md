# BetterCompare – One Search. Every Comparison.

· [📊 Dashboard](https://bettercompare.dev/dashboard) · [🧪 Widget Sandbox](https://bettercompare.dev/dashboard)

> 🇩🇪 **Deutsche Version** weiter unten / German version below

---

## Intro

The project grabbed me from the start: how do you bring multiple independent APIs together in a way that an AI model like ChatGPT can use them cleanly and reliably without chaos, naming conflicts, or blind spots? That's exactly what I set out to solve with BetterCompare — a ChatGPT-native MCP proxy that aggregates multiple comparison verticals into a single unified interface, powered by a conformance engine, live monitoring, and structured developer feedback.

It was my first time diving deep into the MCP protocol, and I quickly realized how much care it takes to make tools truly ChatGPT-ready: clear descriptions, consistent schemas, meaningful error messages. What looks like a simple routing problem at first glance turns into a question of architecture and trust — the proxy needs to work as a reliable gatekeeper, not just a pass-through.

The heart ❤️ of the project is the Conformance Engine: it validates every tool against structured rules and gives vertical teams concrete, actionable feedback. Not just a rejection, but a clear "here's the problem, and here's how to fix it." That part was especially satisfying to build.

---

## 📋 Table of Contents

- [Intro](#intro)
- [🚀 Live Demo](#-live-demo)
- [🔍 How to Test](#-how-to-test)
- [📁 Repository Structure](#-repository-structure)
- [🏗️ Architecture](#️-architecture)
- [🔌 API Reference](#-api-reference)
- [⭐ Optional Features](#-optional-features)
- [🔒 Security Considerations](#-security-considerations)
- [☁️ Deployment](#️-deployment)
- [🚧 Known Limitations](#-known-limitations--trade-offs)
- [🧠 Key Design Decisions](#-key-design-decisions)
- [🎓 Learnings & Reflections](#-learnings--reflections)
- [📚 Documentation](#-documentation)
- [🇩🇪 Deutsche Version](#-deutsche-version)

---

## 🚀 Live Demo

| Service | URL |
|---|---|
| 📊 Monitoring Dashboard | https://bettercompare.dev/dashboard |
| 🧪 Widget Sandbox | https://bettercompare.dev/dashboard (Sandbox Tab) |
| 🔍 OpenAPI Schema | https://bettercompare.dev/openapi-schema |
| 💬 Feedback | https://bettercompare.dev/feedback |
| 📋 Catalog | https://bettercompare.dev/catalog |
| 🔢 Versions | https://bettercompare.dev/versions |
| 📡 Traces | https://bettercompare.dev/traces |
| ❤️ Health | https://bettercompare.dev/health |
| 🌐 Proxy MCP Endpoint | https://bettercompare.dev/mcp |

> ⚠️ ChatGPT connects **only** to the proxy MCP. All vertical MCPs run internally and are never exposed directly.

---

## 🔍 How to Test

```bash
# 1. Check vertical health
curl https://bettercompare.dev/health

# 2. Connect MCP Inspector
npx @modelcontextprotocol/inspector https://bettercompare.dev/mcp

# 3. See conformance feedback
curl https://bettercompare.dev/feedback?vertical=insurance

# 4. Open the dashboard
https://bettercompare.dev/dashboard

# 5. Test any tool in the Widget Sandbox
https://bettercompare.dev/dashboard → Widget Sandbox Tab → Select tool → Run
```

---

## 📁 Repository Structure

```
BetterCompare/
├── proxy/
│   ├── main.py                  ← MCP proxy core
│   ├── requirements.txt
│   ├── conformance/
│   │   └── engine.py            ← Rule engine (schema, safety, naming, UX)
│   ├── monitoring/
│   │   ├── tracer.py            ← Per-request tracing with correlation IDs
│   │   ├── stats.py             ← Metrics aggregation per vertical
│   │   └── session_store.py     ← Session-level tool usage tracking
│   ├── feedback/
│   │   └── store.py             ← Actionable feedback per vertical team
│   ├── catalog/
│   │   └── versions.py          ← Versioning + breaking change detection
│   ├── dashboard/
│   │   ├── index.html           ← Live monitoring dashboard + Widget Sandbox
│   │   └── BetterCompare.png    ← Logo
│   └── verticals/
│       ├── internet/main.py     ← Port 8801
│       ├── mobile/main.py       ← Port 8802
│       ├── travel/main.py       ← Port 8803
│       └── insurance/main.py    ← Port 8804
├── docs/
│   ├── EN_01_overview.md
│   ├── EN_02_conformance.md
│   ├── EN_03_versioning.md
│   ├── EN_04_qa_monitoring.md
│   ├── DE_01_uebersicht.md
│   └── DE_02_conformance_versioning_qa.md
├── Dockerfile
├── start.sh
└── privacy.md
```

---

## 🏗️ Architecture

```
ChatGPT / MCP Inspector
         │
         ▼
┌────────────────────────────────────┐
│      BetterCompare MCP Proxy       │
│        bettercompare.dev           │
│                                    │
│  ┌─────────────┐ ┌──────────────┐  │
│  │ Conformance │ │   Routing    │  │
│  │   Engine    │ │ + Namespace  │  │
│  └─────────────┘ └──────────────┘  │
│  ┌─────────────┐ ┌──────────────┐  │
│  │  Monitoring │ │   Feedback   │  │
│  │  + Tracing  │ │   Engine     │  │
│  └─────────────┘ └──────────────┘  │
└──────────────┬─────────────────────┘
               │ internal only (MCP SDK ClientSession)
    ┌──────────┼──────────┬──────────┐
    ▼          ▼          ▼          ▼
 :8801      :8802      :8803      :8804
Internet   Mobile     Travel   Insurance
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/mcp` | POST | MCP endpoint for ChatGPT |
| `/mcp?vertical=internet` | POST | QA mode — only internet tools |
| `/health` | GET | Vertical reachability |
| `/catalog` | GET | Full tool catalog |
| `/feedback` | GET | Conformance feedback (all verticals) |
| `/feedback?vertical=X` | GET | Feedback for one vertical |
| `/traces` | GET | Recent tool call traces |
| `/stats` | GET | Aggregated metrics |
| `/sessions` | GET | Session-level tool usage |
| `/versions` | GET | Version manifest |
| `/versions/check?vertical=X` | GET | Per-vertical version status |
| `/dashboard` | GET | Live monitoring dashboard + Widget Sandbox |
| `/validate` | POST | Dry-run conformance check for any tool |
| `/reload` | POST | Invalidate tool cache |
| `/openapi-schema` | GET | OpenAPI schema for ChatGPT Actions |

### Per-Vertical QA Mode
```bash
POST https://bettercompare.dev/mcp?vertical=internet

# Via header
POST https://bettercompare.dev/mcp
x-vertical: internet
```

### Connecting to ChatGPT
1. Go to [chatgpt.com/gpts/editor](https://chatgpt.com/gpts/editor)
2. Click **Configure** → **Actions** → **Add actions**
3. Click **Import from URL** and enter: `https://bettercompare.dev/openapi-schema`
4. ChatGPT will discover all tools automatically

---

## ⭐ Optional Features

### Cross-Vertical Namespacing
All tools are namespaced as `vertical__tool_name`:
- `internet__compare_internet_offers`
- `travel__search_flights`

Prevents naming conflicts. ChatGPT always knows which vertical owns which tool.

### Live Monitoring Dashboard + AI Assistant

`https://bettercompare.dev/dashboard`

Shows:
- Total tools + conformance score
- Vertical health (green/amber/red)
- Conformance violations with fix suggestions
- Live trace timeline
- Session flows
- Top tools by usage
- **AI Assistant** — ask BetterCompare anything in natural language, it routes to the right vertical tool automatically

### 🧪 Widget Sandbox

`https://bettercompare.dev/dashboard` → Widget Sandbox tab

Vertical teams can test any tool in isolation — through the same proxy path ChatGPT uses. Select a tool, fill in parameters, see the live result with widget preview and raw JSON.

### Session-Level Insights
`GET /sessions` tracks tool usage across a conversation:

```json
{
  "session_id": "sess_abc123",
  "flow": "internet__compare_internet_offers → travel__search_flights",
  "total_calls": 2,
  "verticals_used": ["internet", "travel"]
}
```

### Structured Tracing
Every tool call gets a `correlation_id` with per-step latency:

```json
{
  "correlation_id": "req_a3f9",
  "tool_name": "internet__compare_internet_offers",
  "total_ms": 142,
  "steps": [{"name": "vertical_call", "at_ms": 11}],
  "status": "ok"
}
```

### Dry-Run Validator
```bash
POST /validate
{
  "vertical": "insurance",
  "tool": { "name": "get_quote", "description": "...", "input_schema": {...} }
}
```

---

## 🔒 Security Considerations

- **Tool exposure**: Conformance layer blocks admin/debug tools from leaking to ChatGPT
- **Input validation**: JSON Schema validation on every tool call
- **Trust boundaries**: Proxy trusts vertical responses at application level. Production would use mTLS between proxy and verticals
- **No auth on proxy**: Correct for developer/connector mode. Production would add API key or OAuth at gateway layer
- **What to harden next**: Rate limiting per session, request size limits, circuit breakers for unreachable verticals, audit logging

---

## ☁️ Deployment

Runs as a single Docker container on Railway:

```bash
docker build -t bettercompare .
docker run -p 8787:8787 bettercompare
```

Deployed at: **https://bettercompare.dev**

---

## 🚧 Known Limitations & Trade-offs

| What | Simplified | Production improvement |
|---|---|---|
| Trace storage | In-memory | ClickHouse or Grafana Tempo |
| Session state | In-memory | Redis with TTL |
| Vertical auth | None | mTLS per vertical |
| Ambiguity resolution | Namespacing only | ML-based intent classifier |
| Conformance scoring | Heuristic | ML-assisted |

---

## 🧠 Key Design Decisions

**Proxy as Gatekeeper**: All tools pass through validation before exposure. Vertical teams get structured, actionable feedback — not just rejection.

**Vertical Independence**: Each vertical owns its tools and schemas. The proxy never assumes a global naming scheme.

**Stability over Flexibility**: The proxy absorbs breaking changes so ChatGPT remains stable.

**Separation of Concerns**: The MCP protocol layer is separate from platform logic so the core could be reused with other MCP-compatible hosts like Claude.

**MCP protocol, not REST**: The proxy implements the MCP JSON-RPC protocol directly for the ChatGPT-facing endpoint. The vertical backends use the official MCP Python SDK with Streamable HTTP — so both sides speak real MCP.

---

## 🎓 Learnings & Reflections

**MCP is more than a protocol** — building with the real SDK showed me why Streamable HTTP and tool schemas are so precisely specified.

**Conformance is a product problem** — deciding which rules are fair was harder than building the engine. The two-policy approach (v1 lenient, v2 strict) was the answer.

**Versioning is underrated** — a listed ChatGPT app is approved at a point in time. Explicit versioning is a product requirement, not just a technical nicety.

**What I would do differently**: persistent storage first (Redis), circuit breakers for unreachable verticals, conformance as a standalone CLI tool.

---

## 📚 Documentation

| File | Description |
|---|---|
| [EN_01_overview.md](docs/EN_01_overview.md) | System overview, architecture, tech stack |
| [EN_02_conformance.md](docs/EN_02_conformance.md) | Conformance engine, rules, feedback |
| [EN_03_versioning.md](docs/EN_03_versioning.md) | Versioning process, breaking changes |
| [EN_04_qa_monitoring.md](docs/EN_04_qa_monitoring.md) | Per-vertical QA, tracing, sessions, dashboard |
| [DE_01_uebersicht.md](docs/DE_01_uebersicht.md) | Systemübersicht (Deutsch) |
| [DE_02_conformance_versioning_qa.md](docs/DE_02_conformance_versioning_qa.md) | Conformance, Versioning, QA (Deutsch) |

---

## Outro

I hope BetterCompare demonstrates how I approach complex architecture problems: with a focus on robustness, clear feedback for other teams, and a system that holds up cleanly under real conditions.

*Made with ❤️ by Julia Goihman*

---
---

# 🇩🇪 Deutsche Version

# BetterCompare – Eine Suche. Alle Vergleiche.

[📊 Dashboard](https://bettercompare.dev/dashboard) · [🧪 Widget Sandbox](https://bettercompare.dev/dashboard)

---

## Einleitung

Das Projekt hat mich von Anfang an gepackt: Wie bringt man mehrere unabhängige APIs so zusammen, dass ein KI-Modell wie ChatGPT sie sauber und zuverlässig nutzen kann — ohne Chaos, Namenskonflikte oder Lücken? Genau das wollte ich mit BetterCompare lösen: ein ChatGPT-nativer MCP-Proxy, der mehrere Vergleichs-Verticals in einer einzigen, einheitlichen Schnittstelle aggregiert, unterstützt durch eine Conformance Engine, Live-Monitoring und strukturiertes Entwickler-Feedback.

Es war das erste Mal, dass ich tief in das MCP-Protokoll eingetaucht bin. Ich habe schnell gemerkt, wie viel Sorgfalt es braucht, Tools wirklich ChatGPT-tauglich zu machen: klare Beschreibungen, konsistente Schemas, aussagekräftige Fehlermeldungen. Was auf den ersten Blick wie ein einfaches Routing-Problem wirkt, wird schnell zur Frage von Architektur und Vertrauen.

Das Herzstück ❤️ des Projekts ist die Conformance Engine: Sie prüft jedes Tool gegen strukturierte Regeln und gibt Vertical-Teams konkretes, umsetzbares Feedback — kein stilles Blockieren, sondern ein klares "Hier ist das Problem, und so kannst du es lösen."

---

## 📋 Inhaltsverzeichnis

- [Einleitung](#einleitung)
- [🚀 Live Demo](#-live-demo-1)
- [🔍 Wie testen](#-wie-testen)
- [📁 Repository-Struktur](#-repository-struktur)
- [🏗️ Architektur](#️-architektur)
- [🔌 API-Referenz](#-api-referenz)
- [⭐ Optionale Features](#-optionale-features)
- [🔒 Sicherheitsüberlegungen](#-sicherheitsüberlegungen)
- [☁️ Deployment](#️-deployment-1)
- [🚧 Bekannte Limitierungen](#-bekannte-limitierungen)
- [🧠 Wichtige Design-Entscheidungen](#-wichtige-design-entscheidungen)
- [🎓 Learnings & Reflexionen](#-learnings--reflexionen)
- [📚 Dokumentation](#-dokumentation-1)

---

## 🚀 Live Demo

| Service | URL |
|---|---|
| 📊 Monitoring Dashboard | https://bettercompare.dev/dashboard |
| 🧪 Widget Sandbox | https://bettercompare.dev/dashboard (Sandbox Tab) |
| 🔍 OpenAPI Schema | https://bettercompare.dev/openapi-schema |
| 💬 Feedback | https://bettercompare.dev/feedback |
| 📋 Katalog | https://bettercompare.dev/catalog |
| 🔢 Versionen | https://bettercompare.dev/versions |
| 📡 Traces | https://bettercompare.dev/traces |
| ❤️ Health | https://bettercompare.dev/health |
| 🌐 Proxy MCP Endpoint | https://bettercompare.dev/mcp |

---

## 🔍 Wie testen

```bash
curl https://bettercompare.dev/health
npx @modelcontextprotocol/inspector https://bettercompare.dev/mcp
curl https://bettercompare.dev/feedback?vertical=insurance
https://bettercompare.dev/dashboard
```

---

## 🏗️ Architektur

```
ChatGPT / MCP Inspector
         │
         ▼
┌────────────────────────────────────┐
│      BetterCompare MCP Proxy       │
│        bettercompare.dev           │
│                                    │
│  ┌─────────────┐ ┌──────────────┐  │
│  │ Conformance │ │   Routing    │  │
│  │   Engine    │ │ + Namespace  │  │
│  └─────────────┘ └──────────────┘  │
│  ┌─────────────┐ ┌──────────────┐  │
│  │  Monitoring │ │   Feedback   │  │
│  │  + Tracing  │ │   Engine     │  │
│  └─────────────┘ └──────────────┘  │
└──────────────┬─────────────────────┘
               │ intern (MCP SDK ClientSession)
    ┌──────────┼──────────┬──────────┐
    ▼          ▼          ▼          ▼
 :8801      :8802      :8803      :8804
Internet   Mobile     Travel   Insurance
```

---

## 🔌 API-Referenz

| Endpoint | Methode | Beschreibung |
|---|---|---|
| `/mcp` | POST | MCP-Endpoint für ChatGPT |
| `/health` | GET | Erreichbarkeit der Verticals |
| `/catalog` | GET | Vollständiger Tool-Katalog |
| `/feedback?vertical=X` | GET | Feedback für ein Vertical |
| `/traces` | GET | Aktuelle Tool-Call-Traces |
| `/versions` | GET | Versions-Manifest |
| `/dashboard` | GET | Live-Dashboard + Widget Sandbox |
| `/validate` | POST | Dry-Run Conformance-Check |

---

## ⭐ Optionale Features

**Cross-Vertical Namespacing** — alle Tools als `vertical__tool_name`, verhindert Namenskonflikte.

**Live Monitoring Dashboard + KI-Assistent** — zeigt Health, Conformance, Traces, Sessions, Top Tools und einen KI-Assistenten der natürlichsprachliche Fragen ans richtige Vertical weiterleitet.

**Widget Sandbox** — Tools isoliert testen über denselben Proxy-Pfad den ChatGPT nutzt.

**Session-Level Insights & Structured Tracing** — jeder Tool-Aufruf bekommt eine `correlation_id`, Sessions tracken Tool-Nutzung über ein Gespräch hinweg.

**Dry-Run Validator** — Tool-Definitionen vor dem Deployment prüfen ohne den Live-Katalog zu berühren.

---

## 🔒 Sicherheitsüberlegungen

- Conformance blockiert Admin/Debug-Tools vor Exposition
- JSON Schema Validierung bei jedem Tool-Call
- Produktion würde mTLS zwischen Proxy und Verticals verwenden
- Was als nächstes gehärtet werden sollte: Rate Limiting, Circuit Breakers, Audit Logging

---

## ☁️ Deployment

```bash
docker build -t bettercompare .
docker run -p 8787:8787 bettercompare
```

Deployed unter: **https://bettercompare.dev**

---

## 🚧 Bekannte Limitierungen

| Was | Vereinfacht | Produktion |
|---|---|---|
| Trace-Speicherung | In-Memory | ClickHouse / Redis |
| Vertical-Auth | Keine | mTLS |
| Ambiguity Resolution | Namespacing | ML Intent Classifier |

---

## 🧠 Wichtige Design-Entscheidungen

**Proxy als Gatekeeper** — strukturiertes Feedback statt stiller Ablehnung.

**Vertical Independence** — jedes Vertical besitzt seine Tools, der Proxy modifiziert keine Namen.

**Stabilität über Flexibilität** — Proxy absorbiert Breaking Changes damit ChatGPT stabil bleibt.

**Separation of Concerns** — Protokoll-Layer getrennt von Business-Logik, wiederverwendbar mit jedem MCP-Host.

---

## 🎓 Learnings & Reflexionen

**MCP ist mehr als ein Protokoll** — erst beim Bauen wurde klar warum Tool-Schemas so präzise spezifiziert sind.

**Conformance ist ein Produkt-Problem** — die richtigen Regeln zu definieren war schwieriger als die Engine zu bauen.

**Versioning ist unterschätzt** — eine gelistete ChatGPT-App wird zu einem Zeitpunkt genehmigt. Explizites Versioning ist eine Produktanforderung.

**Was ich anders machen würde**: persistente Speicherung von Anfang an, Circuit Breaker, Conformance als eigenständiges CLI-Tool.

---

## 📚 Dokumentation

| Datei | Beschreibung |
|---|---|
| [EN_01_overview.md](docs/EN_01_overview.md) | System overview, architecture |
| [EN_02_conformance.md](docs/EN_02_conformance.md) | Conformance engine, rules |
| [EN_03_versioning.md](docs/EN_03_versioning.md) | Versioning process |
| [EN_04_qa_monitoring.md](docs/EN_04_qa_monitoring.md) | QA, tracing, sessions |
| [DE_01_uebersicht.md](docs/DE_01_uebersicht.md) | Systemübersicht (DE) |
| [DE_02_conformance_versioning_qa.md](docs/DE_02_conformance_versioning_qa.md) | Conformance, Versioning, QA (DE) |

---

## Outro

Ich hoffe, BetterCompare zeigt, wie ich komplexe Architektur-Probleme angehe: mit Fokus auf Robustheit, klarem Feedback für andere Teams und einem System das unter realen Bedingungen standhält.

*Made with ❤️ by Julia Goihman*

