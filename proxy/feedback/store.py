from datetime import datetime
from collections import defaultdict

class FeedbackStore:
    def __init__(self):
        self._data = defaultdict(list)
        self._catalog = []

    def record(self, vertical: str, tool: dict, report: dict):
        tool_name = tool.get("name", "unknown")
        qualified_name = f"{vertical}__{tool_name}"

        entry = {
            "vertical": vertical,
            "tool": tool_name,
            "qualified_name": qualified_name,
            "status": report["status"],
            "score": report["score"],
            "violations": report["violations"],
            "checked_at": report["checked_at"]
        }

        # Update feedback per vertical
        self._data[vertical] = [
            e for e in self._data[vertical]
            if e["tool"] != tool_name
        ]
        self._data[vertical].append(entry)

        # Update catalog
        self._catalog = [
            e for e in self._catalog
            if e["qualified_name"] != qualified_name
        ]
        self._catalog.append(entry)

    def get(self, vertical: str = None):
        if vertical:
            entries = self._data.get(vertical, [])
            return {
                "vertical": vertical,
                "total": len(entries),
                "accepted": sum(1 for e in entries if e["status"] == "accepted"),
                "adapted": sum(1 for e in entries if e["status"] == "adapted"),
                "blocked": sum(1 for e in entries if e["status"] == "blocked"),
                "score": round(
                    sum(e["score"] for e in entries) / len(entries)
                    if entries else 0
                ),
                "tools": entries
            }

        # All verticals
        all_entries = list(self._catalog)
        return {
            "total": len(all_entries),
            "accepted": sum(1 for e in all_entries if e["status"] == "accepted"),
            "adapted": sum(1 for e in all_entries if e["status"] == "adapted"),
            "blocked": sum(1 for e in all_entries if e["status"] == "blocked"),
            "overall_score": round(
                sum(e["score"] for e in all_entries) / len(all_entries)
                if all_entries else 0
            ),
            "by_vertical": {
                v: self.get(v) for v in self._data.keys()
            }
        }

    def get_catalog(self):
        return sorted(
            self._catalog,
            key=lambda x: x["score"]
        )
def clear(self):
    self._data.clear()
    self._catalog.clear()
    
# Global instance
feedback_store = FeedbackStore()
