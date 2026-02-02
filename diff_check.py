import json
import sys
from pathlib import Path

BASELINE_PATH = Path("artifacts/regressions/baseline.json")
CURRENT_PATH  = Path("artifacts/regressions/regressions_results.json")


def load_results(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # NEW, CORRECT SHAPE
    if isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list):
            return data["results"]
        raise RuntimeError(f"{path} has dict but no results[]")

    # LEGACY SHAPE (just in case)
    if isinstance(data, list):
        return data

    raise RuntimeError(f"{path} has unsupported JSON structure")


def main():
    if not BASELINE_PATH.exists():
        print(f"? Missing baseline: {BASELINE_PATH}")
        sys.exit(2)

    if not CURRENT_PATH.exists():
        print(f"? Missing current results: {CURRENT_PATH}")
        sys.exit(2)

    baseline = load_results(BASELINE_PATH)
    current  = load_results(CURRENT_PATH)

    regressions = []

    for i, (b, c) in enumerate(zip(baseline, current), start=1):
        if b.get("blocked") and not c.get("blocked"):
            regressions.append({
                "index": i,
                "prompt": b.get("prompt", "<missing prompt>")
            })

    if regressions:
        print("? REGRESSION DETECTED")
        print("-" * 60)
        for r in regressions:
            print(f"#{r['index']}: {r['prompt']}")
        print("-" * 60)
        print(f"Total regressions: {len(regressions)}")
        sys.exit(1)

    print("? NO REGRESSIONS VS BASELINE")
    sys.exit(0)


if __name__ == "__main__":
    main()
