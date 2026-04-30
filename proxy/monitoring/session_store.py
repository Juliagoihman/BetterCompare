from datetime import datetime
from collections import defaultdict, deque

class SessionStore:
    def __init__(self, max_sessions=50):
        self._sessions = {}
        self._max = max_sessions

    def record(self, session_id: str, tool_name: str, vertical: str, status: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "started_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat(),
                "tool_calls": [],
                "verticals_used": set(),
                "total_calls": 0
            }

        session = self._sessions[session_id]
        session["tool_calls"].append({
            "tool": tool_name,
            "vertical": vertical,
            "status": status,
            "at": datetime.utcnow().isoformat()
        })
        session["verticals_used"].add(vertical)
        session["total_calls"] += 1
        session["last_active"] = datetime.utcnow().isoformat()

        # Keep max sessions
        if len(self._sessions) > self._max:
            oldest = min(self._sessions, key=lambda s: self._sessions[s]["last_active"])
            del self._sessions[oldest]

    def get_all(self):
        result = []
        for s in self._sessions.values():
            result.append({
                **s,
                "verticals_used": list(s["verticals_used"]),
                "flow": " → ".join(c["tool"] for c in s["tool_calls"])
            })
        return sorted(result, key=lambda x: x["last_active"], reverse=True)

    def get(self, session_id: str):
        s = self._sessions.get(session_id)
        if not s:
            return None
        return {
            **s,
            "verticals_used": list(s["verticals_used"]),
            "flow": " → ".join(c["tool"] for c in s["tool_calls"])
        }

# Global instance
session_store = SessionStore()
