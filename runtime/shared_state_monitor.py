# shared_state_monitor.py
# Drop-in "Chain of Tool Intents" monitor to catch fragmented multi-agent intent

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re
import time

ENUM_TOOLS = {"list_files", "ls", "readdir", "glob"}
READ_TOOLS = {"read_file", "cat", "open_file"}

SENSITIVE_NAME_RE = re.compile(
    r"(^|[\\/])\.(env(\..*)?|ssh|npmrc|pypirc|git-credentials)$"
    r"|(^|[\\/])\.(aws|gnupg)([\\/]|$)"
    r"|(^|[\\/])\.git([\\/]|$)"
    r"|(^|[\\/])kubeconfig$"
    r"|(^|[\\/])id_(rsa|ed25519)(\.pub)?$"
    r"|(^|[\\/])(credentials|secret|secrets|token|tokens|apikey|api_key|private_key)([\\/]|$)?",
    re.IGNORECASE,
)

INDEX_SEL_RE = re.compile(
    r"\b(file\s*)?#\s*(\d+)\b|\bindex\s*(\d+)\b|\bthe\s*(\d+)(st|nd|rd|th)\b",
    re.IGNORECASE,
)

RECENT_WINDOW_EVENTS = 8
CHALLENGE_THRESHOLD = 3.0
BLOCK_THRESHOLD = 5.0

@dataclass
class ToolEvent:
    ts: float
    agent_id: str
    tool_name: str
    args: Dict[str, Any]

@dataclass
class RunState:
    run_id: str
    events: List[ToolEvent] = field(default_factory=list)
    last_dir_listing: Optional[List[str]] = None
    last_dir_path: Optional[str] = None

class SharedStateMonitor:
    def __init__(self) -> None:
        self._runs: Dict[str, RunState] = {}

    def _run(self, run_id: str) -> RunState:
        if run_id not in self._runs:
            self._runs[run_id] = RunState(run_id=run_id)
        return self._runs[run_id]

    @staticmethod
    def _is_enum(tool_name: str) -> bool:
        return tool_name in ENUM_TOOLS

    @staticmethod
    def _is_read(tool_name: str) -> bool:
        return tool_name in READ_TOOLS

    @staticmethod
    def _mentions_index_selection(nl_request: str) -> Tuple[bool, Optional[int]]:
        if not nl_request:
            return (False, None)
        m = INDEX_SEL_RE.search(nl_request)
        if not m:
            return (False, None)

        file_hash = m.group(2)
        idx_word = m.group(3)
        ordinal = m.group(4)

        if idx_word is not None:
            return (True, int(idx_word))
        if file_hash is not None:
            return (True, int(file_hash) - 1)
        if ordinal is not None:
            return (True, int(ordinal) - 1)
        return (True, None)

    @staticmethod
    def _looks_sensitive(path_or_name: str) -> bool:
        return bool(path_or_name and SENSITIVE_NAME_RE.search(path_or_name))

    @staticmethod
    def _recent_enum_agent(run: RunState) -> Optional[str]:
        for e in reversed(run.events[-RECENT_WINDOW_EVENTS:]):
            if SharedStateMonitor._is_enum(e.tool_name):
                return e.agent_id
        return None

    def preflight(
        self,
        run_id: str,
        agent_id: str,
        tool_name: str,
        args: Dict[str, Any],
        nl_request: str = "",
    ) -> Dict[str, Any]:
        run = self._run(run_id)
        reasons: List[str] = []
        score = 0.0
        resolved_target: Optional[str] = None

        recent_enum = any(self._is_enum(e.tool_name) for e in run.events[-RECENT_WINDOW_EVENTS:])
        if recent_enum:
            score += 1.0
            reasons.append("recent directory enumeration in this run")

        if recent_enum:
            enum_agent = self._recent_enum_agent(run)
            if enum_agent and enum_agent != agent_id:
                score += 1.0
                reasons.append(f"cross-agent chain: enum by {enum_agent}, action by {agent_id}")

        nl_has_index, nl_index = self._mentions_index_selection(nl_request)
        args_has_index = "index" in args or "file_index" in args

        if nl_has_index or args_has_index:
            score += 2.0
            reasons.append("index-based file selection (indirection)")

        if self._is_read(tool_name):
            target = args.get("path") or args.get("filepath") or args.get("file")

            idx = None
            if "index" in args:
                idx = int(args["index"])
            elif "file_index" in args:
                idx = int(args["file_index"])
            elif nl_has_index and nl_index is not None:
                idx = nl_index

            if not target and idx is not None and run.last_dir_listing:
                if 0 <= idx < len(run.last_dir_listing):
                    resolved_target = run.last_dir_listing[idx]
                    target = resolved_target
                    reasons.append(f"resolved index {idx} -> {target}")
                else:
                    score += 1.0
                    reasons.append("index out of bounds for last listing")

            if target:
                if self._looks_sensitive(str(target)):
                    score += 5.0
                    reasons.append(f"target looks sensitive: {target}")

                if re.search(r"(^~|^/|^[A-Za-z]:\\|[\\/]\.)", str(target)):
                    score += 1.0
                    reasons.append("read path is root/home/hidden-ish")

        # Hard rule: enumeration -> index-based read
        if recent_enum and (nl_has_index or args_has_index) and self._is_read(tool_name):
            return {
                "decision": "block",
                "score": 999.0,
                "reasons": reasons + ["hard rule: no index-based reads after enumeration"],
                "resolved_target": resolved_target,
            }

        decision = "allow"
        if score >= BLOCK_THRESHOLD:
            decision = "block"
        elif score >= CHALLENGE_THRESHOLD:
            decision = "challenge"

        return {"decision": decision, "score": score, "reasons": reasons, "resolved_target": resolved_target}

    def on_result(
        self,
        run_id: str,
        agent_id: str,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
    ) -> None:
        run = self._run(run_id)
        run.events.append(ToolEvent(ts=time.time(), agent_id=agent_id, tool_name=tool_name, args=dict(args)))

        if self._is_enum(tool_name):
            listing: Optional[List[str]] = None
            if isinstance(result, dict):
                for k in ("files", "paths", "entries"):
                    if k in result and isinstance(result[k], list):
                        listing = [str(x) for x in result[k]]
                        break
            elif isinstance(result, list):
                listing = [str(x) for x in result]

            if listing is not None:
                run.last_dir_listing = listing
                run.last_dir_path = str(args.get("path") or args.get("dir") or args.get("directory") or "")

