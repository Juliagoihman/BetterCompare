from datetime import datetime
from collections import defaultdict

class Stats:
    def __init__(self):
        self._calls = defaultdict(int)
        self._errors = defaultdict(int)
        self._tool_usage = defaultdict(int)
        self._conformance = defaultdict(lambda: {
            "accepted": 0,
            "adapted": 0,
            "blocked": 0
        })
        self._started_at = datetime.utcnow().isoformat()

    def record_call(self, vertical: str, tool_name: str):
        self._calls[vertical] += 1
        self._tool_usage[tool_name] += 1

    def record_error(self, vertical: str):
        self._errors[vertical] += 1

    def record_tool(self, vertical: str, status: str):
        self._conformance[vertical][status] += 1

    def get_all(self):
        verticals = {}
        all_verticals = set(
            list(self._calls.keys()) +
            list(self._errors.keys()) +
            list(self._conformance.keys())
        )

        for v in all_verticals:
            calls = self._calls[v]
            errors = self._errors[v]
            error_rate = round(
                (errors / calls * 100) if calls > 0 else 0, 1
            )
            verticals[v] = {
                "calls": calls,
                "errors": errors,
                "error_rate_pct": error_rate,
                "conformance": self._conformance[v]
            }

        total_calls = sum(self._calls.values())
        total_errors = sum(self._errors.values())

        return {
            "started_at": self._started_at,
            "total_calls": total_calls,
            "total_errors": total_errors,
            "top_tools": sorted(
                self._tool_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "verticals": verticals
        }
def get_all(self):
    total_calls = sum(self._calls.values())
    total_errors = sum(self._errors.values())

    # Neu: success count
    total_success = total_calls - total_errors

    return {
        "started_at": self._started_at,
        "total_calls": total_calls,
        "total_errors": total_errors,
        "total_success": total_success,  # NEU
        "success_rate_pct": round(
            (total_success / total_calls * 100) if total_calls > 0 else 100, 1
        ),  # NEU
        "top_tools": sorted(
            self._tool_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10],
        "verticals": verticals
    }
# Global instance
stats = Stats()
