# BetterCompare — Conformance Engine

## Was ist die Conformance Engine?

Die Conformance Engine ist der Türsteher des Systems. Bevor ein Tool eines Verticals ChatGPT erreicht, muss es eine Reihe strukturierter Regeln bestehen. Tools die scheitern werden entweder angepasst (mit Warnung) oder komplett blockiert.

Das schützt ChatGPT davor, fehlerhafte, unsichere oder verwirrende Tools zu erhalten — und gibt Vertical-Teams klares, umsetzbares Feedback was zu verbessern ist.

---

## Wie es funktioniert

Beim Start verbindet sich der Proxy mit jedem Vertical und lädt seine Tools. Für jedes Tool durchläuft er die Regelliste:

```
Tool vom Vertical
      │
      ▼
┌─────────────────────────────┐
│  Regel: MISSING_NAME?       → FEHLER   → blockiert
│  Regel: MISSING_SCHEMA?     → FEHLER   → blockiert
│  Regel: MISSING_DESCRIPTION?→ WARNUNG  → angepasst
│  Regel: ADMIN_TOOL?         → FEHLER   → blockiert
│  Regel: NAMING_SNAKE_CASE?  → WARNUNG  → angepasst
│  Regel: MISSING_REQUIRED?   → WARNUNG  → angepasst
└─────────────────────────────┘
      │
      ▼
Status: accepted / adapted / blocked
```

---

## Die Regeln

| Regel-ID | Gruppe | Schwere | Was wird geprüft |
|----------|--------|---------|------------------|
| `MISSING_NAME` | schema | FEHLER | Tool muss einen Namen haben |
| `MISSING_SCHEMA` | schema | FEHLER | Tool muss ein Input-Schema haben |
| `MISSING_DESCRIPTION` | schema | WARNUNG | Beschreibung muss mindestens 10 Zeichen haben |
| `ADMIN_TOOL` | safety | FEHLER | Namen wie "admin", "debug", "internal", "test" werden blockiert |
| `NAMING_SNAKE_CASE` | naming | WARNUNG | Tool-Name muss Kleinbuchstaben und Unterstriche verwenden |
| `MISSING_REQUIRED` | ux | WARNUNG | Input-Schema muss Pflichtfelder deklarieren |

---

## Tool-Status

- **accepted** — Tool hat alle Regeln bestanden, wird unverändert exponiert
- **adapted** — Tool hat Warnungen, wird trotzdem exponiert (Policy v1)
- **blocked** — Tool hat Fehler, wird ChatGPT nicht angezeigt

---

## Policy-Versionen

Die Conformance Engine unterstützt zwei Modi:

| Policy | Verhalten |
|--------|-----------|
| `v1` (Standard) | Nachsichtig — Tools mit Warnungen werden angepasst und exponiert |
| `v2` | Streng — Tools mit jeglichen Verstößen werden blockiert |

Vertical-Teams können gegen v2 testen bevor es Standard wird:
```
POST /mcp?version=v2
```

---

## Conformance-Score

Jedes Tool bekommt einen Score von 0–100:
- Jeder FEHLER zieht 30 Punkte ab
- Jede WARNUNG zieht 10 Punkte ab

Der Gesamt-Score eines Verticals ist der Durchschnitt über alle seine Tools.

---

## Feedback für Vertical-Teams

Jeder Verstoß erzeugt einen strukturierten Feedback-Eintrag:

```json
{
  "rule_id": "MISSING_DESCRIPTION",
  "group": "schema",
  "severity": "WARNING",
  "reason": "Tool 'get_insurance_quote' hat keine sinnvolle Beschreibung",
  "fix": "Füge eine Beschreibung mit mindestens 10 Zeichen hinzu"
}
```

Teams können ihr Feedback jederzeit abrufen:
```
GET /feedback?vertical=insurance
```

Das `fix`-Feld ist das Kernfeature — Teams wissen genau was zu ändern ist, nicht nur dass etwas falsch ist.

---

# BetterCompare — Versioning

## Warum Versioning wichtig ist

Eine ChatGPT-App die von OpenAI genehmigt wurde, ist zu einem bestimmten Zeitpunkt registriert. Jede Änderung an Tools, Schemas oder Verhalten kann eine erneute Prüfung erfordern. Stabilität ist nicht nur ein technisches Schmankerl — es ist eine Produktanforderung.

BetterCompare behandelt Versioning als erstklassiges Konzept: jede Komponente hat eine explizite Version, Breaking Changes werden automatisch erkannt, und der Proxy absorbiert Änderungen damit ChatGPT stabil bleibt.

---

## Versions-Manifest

Jede Komponente hat ihre eigene Version:

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

Abrufbar unter: `GET /versions`

---

## Wer macht was bei einer Änderung?

### Vertical-Team liefert eine nicht-brechende Änderung
*(z.B. optionaler Parameter hinzugefügt, Beschreibung verbessert)*

1. Vertical-Team aktualisiert ihren MCP-Server
2. Vertical-Team bumpt ihre Version in `catalog/versions.py`
3. Proxy-Operator ruft `POST /reload` auf um den Katalog zu aktualisieren
4. Kein ChatGPT-Review nötig — nichts was ChatGPT sieht hat sich geändert

### Vertical-Team liefert eine brechende Änderung
*(z.B. neuer Pflichtparameter, Parametertyp geändert)*

1. Der Breaking-Change-Detektor des Proxys markiert die Änderung automatisch
2. Vertical-Team erhält eine strukturierte Warnung via `/feedback`
3. Vertical-Team und Proxy-Operator koordinieren — die Änderung kann nicht live gehen bis ein Migrationspfad vereinbart ist
4. Proxy-Operator bumpt die **Proxy-Major-Version** (`1.0.0` → `2.0.0`)
5. ChatGPT-Review kann erforderlich sein

---

# BetterCompare — Per-Vertical QA & Monitoring

## Per-Vertical QA Mode

### Das Problem

In einem echten Deployment arbeiten mehrere Vertical-Teams unabhängig. Wenn ein Team seine Tools End-to-End durch ChatGPT testen möchte, hat es ein Problem: ChatGPT verbindet sich mit einer Proxy-URL und bekommt alle 14 Tools aller 4 Verticals zurück. Das Team sieht seine 3 Tools vermischt mit allen anderen.

### Die Lösung

Der Proxy unterstützt eine gefilterte Ansicht — er filtert den Tool-Katalog auf nur ein Vertical, während die gleiche Connector-URL verwendet wird.

**Via Query-Parameter:**
```
POST https://bettercompare.dev/mcp?vertical=internet
```

**Via Header:**
```
POST https://bettercompare.dev/mcp
x-vertical: internet
```

### Warum dieser Ansatz?

Drei Alternativen wurden betrachtet:

| Option | Kompromiss |
|--------|------------|
| Separates Deployment pro Vertical | Erfordert Infrastruktur-Änderungen, separate URLs |
| Separate Proxy-Instanz pro Vertical | Gleiches Problem — plus Koordinationsaufwand |
| Query-Param / Header am bestehenden Proxy | Keine Infrastruktur-Änderungen, gleiche Connector-URL |

Der Query-Param / Header Ansatz wurde gewählt weil er keine Änderungen an der ChatGPT-Connector-Konfiguration erfordert.

---

## Monitoring

### Tracing

Jeder Tool-Aufruf bekommt eine eindeutige `correlation_id`. Der Tracer zeichnet auf:
- Welches Tool aufgerufen wurde
- Welches Vertical es bearbeitet hat
- Wie lange jeder Schritt dauerte
- Ob es erfolgreich war oder fehlgeschlagen ist

Abrufbar unter: `GET /traces`

### Stats

Aggregierte Metriken pro Vertical — Aufrufzahlen, Fehlerraten, Conformance-Status.

Abrufbar unter: `GET /stats`

### Sessions

Tool-Nutzung über ein Gespräch hinweg — welche Verticals wurden genutzt, in welcher Reihenfolge, durchschnittliche Latenz.

Die Session-ID kommt aus dem `mcp-session-id` Header den ChatGPT mit jedem Request sendet — das ist der Standard-Weg um Requests innerhalb eines Gesprächs zu korrelieren.

Abrufbar unter: `GET /sessions`

### Dashboard

Alles oben Genannte ist im Live-Dashboard sichtbar:
```
https://bettercompare.dev/dashboard
```
