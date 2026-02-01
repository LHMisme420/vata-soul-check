from __future__ import annotations

from typing import Any, Dict, Callable
from runtime.shared_state_monitor import SharedStateMonitor

# TODO: Replace with your real tool implementations
def list_files(path: str = "."):
    import os
    return {"files": sorted(os.listdir(path))}

def read_file(path: str):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

TOOLS: Dict[str, Callable[..., Any]] = {
    "list_files": list_files,
    "read_file": read_file,
}

monitor = SharedStateMonitor()

def execute_tool(*, run_id: str, agent_id: str, tool_name: str, args: Dict[str, Any], nl_request: str = "") -> Any:
    decision = monitor.preflight(
        run_id=run_id,
        agent_id=agent_id,
        tool_name=tool_name,
        args=args,
        nl_request=nl_request,
    )

    if decision["decision"] == "block":
        raise PermissionError("Blocked tool call: " + "; ".join(decision["reasons"]))

    if decision["decision"] == "challenge":
        return {"error": "clarification_required", "reasons": decision["reasons"]}

    result = TOOLS[tool_name](**args)

    monitor.on_result(
        run_id=run_id,
        agent_id=agent_id,
        tool_name=tool_name,
        args=args,
        result=result,
    )

    return result
