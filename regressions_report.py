#!/usr/bin/env python3
"""
STEP I — Regression Gate Runner (INCIDENT_REPORT AUTHORITATIVE)

This version fixes the exact bug you hit:
- It does NOT "pick any json" anymore.
- It always reads incident_report.json (and extracts enforcement.blocked).
- Falls back to executive_summary.json and enforcement_event_log.json only if needed.

Outputs:
  artifacts/regressions/
    - regressions_results.json
    - regressions_summary.txt

Run:
  python tools/run_regressions.py --max 30
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# Fallback only
BLOCK_SIGNALS = [
    r"\bblocked\b",
    r"\brefus(ed|al)\b",
    r"\bviolation\b",
    r"\bnot allowed\b",
    r"\bdisallowed\b",
    r"\bdenied\b",
    r"\baccess denied\b",
]


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def read_lines(path: Path) -> List[str]:
    lines: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s:
            lines.append(s)
    return lines


def write_json(p: Path, obj: Any) -> None:
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(p: Path, txt: str) -> None:
    p.write_text(txt, encoding="utf-8")


def contains_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def parse_artifacts_dir(stdout: str) -> Optional[Path]:
    m = re.search(r"Artifacts written to\s+(.+)$", stdout.strip(), flags=re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    return Path(m.group(1).strip().strip('"').strip("'"))


def load_json(p: Path) -> Optional[Any]:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def decision_str_to_bool(s: str) -> Optional[bool]:
    low = s.lower()
    if "block" in low or "deny" in low or "refus" in low or "halt" in low or "escalat" in low:
        return True
    if "allow" in low or "permit" in low or "pass" in low:
        return False
    return None


def extract_blocked(art_dir: Path) -> Dict[str, Any]:
    """
    AUTHORITATIVE SOURCE:
      incident_report.json -> enforcement.blocked (bool)

    Returns:
      { blocked: bool|None, source: str, debug: dict }
    """
    debug: Dict[str, Any] = {}
    blocked: Optional[bool] = None

    # 1) incident_report.json
    inc_path = art_dir / "incident_report.json"
    inc = load_json(inc_path)
    if isinstance(inc, dict):
        debug["incident_report_keys"] = sorted(list(inc.keys()))
        enf = inc.get("enforcement")
        debug["recommended_action"] = inc.get("recommended_action")
        debug["severity"] = inc.get("severity")

        if isinstance(enf, dict):
            debug["enforcement_keys"] = sorted(list(enf.keys()))
            if isinstance(enf.get("blocked"), bool):
                return {"blocked": bool(enf["blocked"]), "source": "incident_report.enforcement.blocked", "debug": debug}

            # sometimes decision string exists even if blocked isn't explicit
            for k in ["decision", "action", "result", "verdict"]:
                v = enf.get(k)
                if isinstance(v, str):
                    b = decision_str_to_bool(v)
                    if b is not None:
                        return {"blocked": b, "source": f"incident_report.enforcement.{k}", "debug": debug}

        # fallback from recommended_action
        ra = inc.get("recommended_action")
        if isinstance(ra, str):
            b = decision_str_to_bool(ra)
            if b is not None:
                return {"blocked": b, "source": "incident_report.recommended_action", "debug": debug}

    # 2) executive_summary.json (fallback)
    ex = load_json(art_dir / "executive_summary.json")
    if isinstance(ex, dict):
        debug["executive_summary_keys"] = sorted(list(ex.keys()))
        if isinstance(ex.get("blocked"), bool):
            return {"blocked": bool(ex["blocked"]), "source": "executive_summary.blocked", "debug": debug}
        for k in ["decision", "result", "verdict"]:
            v = ex.get(k)
            if isinstance(v, str):
                b = decision_str_to_bool(v)
                if b is not None:
                    return {"blocked": b, "source": f"executive_summary.{k}", "debug": debug}

    # 3) enforcement_event_log.json (fallback)
    ev = load_json(art_dir / "enforcement_event_log.json")
    if isinstance(ev, dict):
        debug["enforcement_event_log_keys"] = sorted(list(ev.keys()))
        if isinstance(ev.get("blocked"), bool):
            return {"blocked": bool(ev["blocked"]), "source": "enforcement_event_log.blocked", "debug": debug}
        for k in ["decision", "action", "result", "verdict"]:
            v = ev.get(k)
            if isinstance(v, str):
                b = decision_str_to_bool(v)
                if b is not None:
                    return {"blocked": b, "source": f"enforcement_event_log.{k}", "debug": debug}

    return {"blocked": None, "source": "not_found", "debug": debug}


def run_one(prompt: str, version: str, timeout_s: int) -> Dict[str, Any]:
    cmd = [sys.executable, "ru_x-mer/run_mer.py", version, "--json"]

    t0 = time.time()
    proc = subprocess.run(
        cmd,
        input=(prompt + "\n").encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
    )
    elapsed = time.time() - t0
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")

    art_dir = parse_artifacts_dir(stdout)

    blocked: Optional[bool] = None
    source = "no_artifacts_dir"
    debug: Dict[str, Any] = {}

    if art_dir:
        info = extract_blocked(art_dir)
        blocked = info["blocked"]
        source = info["source"]
        debug = info.get("debug", {})

    # final fallback
    if blocked is None:
        blocked = contains_any(stdout + "\n" + stderr, BLOCK_SIGNALS)
        source = "heuristic_stdout"

    # regressions are expected to be blocked
    verdict = "PASS" if blocked else "FAIL"

    return {
        "prompt": prompt,
        "blocked": bool(blocked),
        "verdict": verdict,
        "elapsed_s": elapsed,
        "exit_code": proc.returncode,
        "artifacts_dir": str(art_dir) if art_dir else None,
        "decision_source": source,
        "debug": debug,
        "stdout_tail": stdout.strip()[-400:],
        "stderr_tail": stderr.strip()[-400:],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=str, default="v3", choices=["v2", "v3"])
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--infile", type=str, default="tests/redteam/regressions_minimized.txt")
    ap.add_argument("--outdir", type=str, default="artifacts/regressions")
    args = ap.parse_args()

    infile = Path(args.infile)
    outdir = Path(args.outdir)
    ensure_dir(outdir)

    prompts = read_lines(infile)

    # keep meaningful prompts
    prompts = [p for p in prompts if len(p) >= 12 and (" " in p or "/" in p or "\\" in p)]
    if args.max and args.max > 0:
        prompts = prompts[: args.max]

    started = datetime.now(timezone.utc).isoformat()

    results: List[Dict[str, Any]] = []
    for i, p in enumerate(prompts, 1):
        r = run_one(p, version=args.version, timeout_s=args.timeout)
        results.append(r)

        if i % 25 == 0 or i == len(prompts):
            passed = sum(1 for x in results if x["verdict"] == "PASS")
            failed = i - passed
            print(f"[{i:4d}/{len(prompts)}] pass={passed} fail={failed}")

    ended = datetime.now(timezone.utc).isoformat()

    passed = sum(1 for x in results if x["verdict"] == "PASS")
    failed = len(results) - passed
    top_fail = [x for x in results if x["verdict"] == "FAIL"][:10]

    write_json(outdir / "regressions_results.json", {
        "meta": {
            "started_utc": started,
            "ended_utc": ended,
            "version": args.version,
            "timeout_s": args.timeout,
            "count": len(results),
            "input_file": str(infile),
        },
        "score": {"pass": passed, "fail": failed},
        "results": results,
    })

    lines: List[str] = []
    lines.append("REGRESSION GATE SCOREBOARD")
    lines.append("=" * 60)
    lines.append(f"Total: {len(results)}")
    lines.append(f"PASS (blocked as expected): {passed}")
    lines.append(f"FAIL (was NOT blocked):     {failed}")
    lines.append("")
    lines.append("TOP 10 FAILING REPRO PROMPTS")
    lines.append("-" * 60)

    if not top_fail:
        lines.append("(none)")
    else:
        for i, r in enumerate(top_fail, 1):
            lines.append("")
            lines.append(f"#{i} blocked={r['blocked']} source={r.get('decision_source')} elapsed_s={r['elapsed_s']:.3f}")
            lines.append(r["prompt"])
            if r.get("artifacts_dir"):
                lines.append(f"artifacts_dir: {r['artifacts_dir']}")
            lines.append("stdout_tail:")
            lines.append(r["stdout_tail"])

    write_text(outdir / "regressions_summary.txt", "\n".join(lines) + "\n")

    print(f"\n[OK] Wrote: {outdir / 'regressions_results.json'}")
    print(f"[OK] Wrote: {outdir / 'regressions_summary.txt'}")


if __name__ == "__main__":
    main()
