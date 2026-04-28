from datetime import datetime
from collections import deque
import time

class Tracer:
    def __init__(self, max_traces=100):
        self._traces = deque(maxlen=max_traces)
        self._active = {}

    def start(self, correlation_id: str, tool_name: str, vertical: str):
        self._active[correlation_id] = {
            "correlation_id": correlation_id,
            "tool_name": tool_name,
            "vertical": vertical,
            "started_at": datetime.utcnow().isoformat(),
            "steps": [],
            "_start_ms": time.time() * 1000
        }

    def step(self, correlation_id: str, step_name: str):
        if correlation_id not in self._active:
            return
        trace = self._active[correlation_id]
        trace["steps"].append({
            "name": step_name,
            "at_ms": round(time.time() * 1000 - trace["_start_ms"])
        })

    def end(self, correlation_id: str, status: str, error: str = None):
        if correlation_id not in self._active:
            return
        trace = self._active.pop(correlation_id)
        total_ms = round(time.time() * 1000 - trace["_start_ms"])

        finished = {
            "correlation_id": trace["correlation_id"],
            "tool_name": trace["tool_name"],
            "vertical": trace["vertical"],
            "started_at": trace["started_at"],
            "total_ms": total_ms,
            "steps": trace["steps"],
            "status": status
        }
        if error:
            finished["error"] = error

        self._traces.appendleft(finished)

    def get_all(self):
        return list(self._traces)

# Global instance
tracer = Tracer()
