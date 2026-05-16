# BetterCompare — Systemübersicht

## Was ist BetterCompare?

BetterCompare ist ein Proxy-Server, der zwischen ChatGPT und mehreren unabhängigen Backend-Diensten (sogenannten "Verticals") sitzt. Jedes Vertical besitzt seine eigenen Tools und Daten. BetterCompare bündelt alle Tools zu einem einzigen Endpunkt, mit dem ChatGPT sich verbinden kann.

```
ChatGPT
   │
   ▼
bettercompare.dev/mcp   ← ein einziger Endpunkt
   │
   ├── internet  (Port 8801)
   ├── mobile    (Port 8802)
   ├── travel    (Port 8803)
   └── insurance (Port 8804)
```

ChatGPT spricht niemals direkt mit den Verticals — nur mit dem Proxy.

---

## Warum gibt es das?

CHECK24 hat viele unabhängige Vergleichsprodukte. Jedes Produkt-Team besitzt seinen eigenen Code und seine eigenen Tools. Aber aus Kundenperspektive ist es eine Marke — eine App, eine Website, ein ChatGPT-Connector.

Der Proxy löst diese Spannung: ein Einstiegspunkt für ChatGPT, unabhängige Ownership für jedes Vertical-Team.

---

## Die 5 Kernkomponenten

### 1. Der Proxy (`proxy/main.py`)
Das Herzstück. Er:
- Verbindet sich beim Start mit jedem Vertical-MCP-Server
- Lädt deren Tools über das MCP-Protokoll
- Prüft jedes Tool durch die Conformance Engine
- Registriert zugelassene Tools unter Namespace-Namen (`internet__compare_internet_offers`)
- Leitet Tool-Aufrufe von ChatGPT an das richtige Vertical weiter
- Trackt jeden Aufruf mit einer Correlation-ID

### 2. Die Conformance Engine (`proxy/conformance/engine.py`)
Ein regelbasierter Validator. Bevor ein Tool ChatGPT erreicht, muss es eine Reihe von Prüfungen bestehen:
- Hat es einen Namen?
- Hat es eine Beschreibung?
- Hat es ein Input-Schema?
- Ist es sicher zu exponieren (keine Admin/Debug-Tools)?
- Folgt es den Namenskonventionen?

Tools die scheitern werden entweder **angepasst** (nur Warnungen) oder **blockiert** (Fehler). Vertical-Teams erhalten strukturiertes Feedback mit einem `fix`-Feld, das genau erklärt was zu ändern ist.

### 3. Versioning (`proxy/catalog/versions.py`)
Jede Komponente hat eine explizite Version:
- Der Proxy selbst (`1.0.0`)
- Jedes Vertical (`internet: 1.2.0`, `insurance: 0.9.0`)
- Der Tool-Katalog (datumgestempelt)

Ein Breaking-Change-Detektor überwacht:
- Neue Pflichtparameter (bestehende ChatGPT-Aufrufe würden brechen)
- Parametertyp-Änderungen (falsche Daten würden gesendet)

Wenn ein Breaking Change erkannt wird, markiert der Proxy ihn bevor er ChatGPT erreicht.

### 4. Per-Vertical QA Mode
Vertical-Teams können ihre Tools isoliert testen — über denselben Proxy-Pfad den ChatGPT nutzt — ohne die Tools aller anderen Verticals zu sehen.

Dies geschieht über einen Query-Parameter oder Header:
```
POST /mcp?vertical=internet
POST /mcp  +  x-vertical: internet
```

Dieser Ansatz wurde gegenüber separaten Deployments gewählt, weil er keine Infrastruktur-Änderungen erfordert und mit der bestehenden Connector-URL funktioniert.

### 5. Monitoring (`proxy/monitoring/`)
Drei Komponenten:
- **Tracer**: weist jedem Tool-Aufruf eine `correlation_id` zu, trackt Latenz pro Schritt
- **Stats**: aggregiert Aufrufzahlen, Fehlerraten und Conformance-Status pro Vertical
- **Session Store**: trackt Tool-Nutzung über ein Gespräch hinweg — welche Verticals wurden genutzt, in welcher Reihenfolge

Alle Daten sind im Live-Dashboard sichtbar: `bettercompare.dev/dashboard`

---

## Technologie-Stack

| Komponente | Technologie |
|------------|-------------|
| MCP-Protokoll | Python MCP SDK (`mcp[cli]`) |
| Transport | Streamable HTTP (MCP-Standard, März 2025) |
| Web-Framework | FastAPI + Starlette |
| HTTP-Client | httpx |
| Deployment | Docker auf Railway |

---

## Live-Endpunkte

| URL | Beschreibung |
|-----|--------------|
| `bettercompare.dev/mcp` | MCP-Endpunkt für ChatGPT |
| `bettercompare.dev/dashboard` | Live-Monitoring-Dashboard |
| `bettercompare.dev/health` | Erreichbarkeit der Verticals |
| `bettercompare.dev/catalog` | Vollständiger Tool-Katalog |
| `bettercompare.dev/feedback` | Conformance-Feedback |
| `bettercompare.dev/traces` | Request-Traces |
| `bettercompare.dev/sessions` | Session-Level Tool-Nutzung |
| `bettercompare.dev/versions` | Versions-Manifest |
