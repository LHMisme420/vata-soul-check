import re
from dataclasses import dataclass
from typing import List, Dict, Any

import gradio as gr


# =========================
#   SOUL SIGNAL ENGINE
# =========================

@dataclass
class SoulSignal:
    comment_density: float
    todo_count: int
    debug_artifacts: int
    magic_numbers: int
    naming_weirdness: float
    line_count: int
    avg_line_length: float


COMMENT_RE = re.compile(r'^\s*#')
TODO_RE = re.compile(r'\bTODO\b', re.IGNORECASE)
DEBUG_RE = re.compile(r'\bprint\(')
MAGIC_NUMBER_RE = re.compile(r'\b\d+\b')


def extract_soul_signal(code: str) -> SoulSignal:
    lines: List[str] = code.splitlines()
    non_empty = [l for l in lines if l.strip()]
    line_count = len(non_empty) or 1

    comments = [l for l in non_empty if COMMENT_RE.search(l)]
    comment_density = len(comments) / line_count

    todo_count = sum(1 for l in non_empty if TODO_RE.search(l))
    debug_artifacts = sum(1 for l in non_empty if DEBUG_RE.search(l))

    magic_numbers = 0
    for l in non_empty:
        if 'for ' in l or 'range(' in l:
            continue
        magic_numbers += len(MAGIC_NUMBER_RE.findall(l))

    avg_line_length = sum(len(l) for l in non_empty) / line_count

    naming_weirdness = 0.0  # placeholder for future ML / naming model

    return SoulSignal(
        comment_density=comment_density,
        todo_count=todo_count,
        debug_artifacts=debug_artifacts,
        magic_numbers=magic_numbers,
        naming_weirdness=naming_weirdness,
        line_count=line_count,
        avg_line_length=avg_line_length,
    )


def score_soul(signal: SoulSignal) -> Dict[str, Any]:
    score = 0.0
    reasons: List[str] = []

    # comments = intent / thinking traces
    score += min(signal.comment_density * 40, 20)

    if signal.todo_count > 0:
        score += 10
        reasons.append("TODO markers detected (future-intent traces).")

    if signal.debug_artifacts > 0:
        score += 20
        reasons.append("Debug prints detected (live debugging traces).")

    if signal.magic_numbers > 0:
        score += min(signal.magic_numbers * 5, 15)
        reasons.append("Magic numbers detected (non-parameterized constants).")

    if signal.line_count < 80:
        score += 10
        reasons.append("Compact snippet (likely hand-written, not boilerplate).")

    score = max(0, min(100, score))

    if score >= 85:
        energy_level = "Full Soul"
    elif score >= 60:
        energy_level = "Partial Soul"
    else:
        energy_level = "Low Soul"

    if score >= 70:
        classification = "HUMAN SOUL"
        verdict = "VATA COMPLIANT"
    elif score >= 40:
        classification = "UNCERTAIN"
        verdict = "REQUIRES REVIEW"
    else:
        classification = "LIKELY SYNTHETIC"
        verdict = "VATA FLAGGED"

    return {
        "score": score,
        "energy_level": energy_level,
        "classification": classification,
        "verdict": verdict,
        "reasons": reasons,
        "raw_signal": signal.__dict__,
    }


def analyze_code(code: str) -> Dict[str, Any]:
    signal = extract_soul_signal(code)
    result = score_soul(signal)
    result["input_code"] = code
    return result


# =========================
#   GRADIO UI
# =========================

EXAMPLE_CODE = """# Human-like messy code with soul
def calculate_something(x):
    # TODO: optimize this later
    result = x * 2 + 42  # magic number from 2am debugging
    print("Debug: ", result)  # left over debug print
    return result
"""


def gradio_analyze(code: str):
    if not code.strip():
        return 0, "Low Soul", "N/A", "No code provided.", "[]", ""
    res = analyze_code(code)
    reasons_str = "\n".join(f"- {r}" for r in res["reasons"]) or "No specific reasons detected."
    return (
        res["score"],
        res["energy_level"],
        res["classification"],
        res["verdict"],
        reasons_str,
        res["input_code"],
    )


with gr.Blocks(title="VATA Soul Check") as demo:
    gr.Markdown("# VATA Soul Check\nScan code for human soul signal.")

    with gr.Row():
        with gr.Column():
            code_in = gr.Code(
                label="Code Input",
                language="python",
                value=EXAMPLE_CODE,
            )
            run_btn = gr.Button("Analyze")

        with gr.Column():
            score_out = gr.Slider(0, 100, value=0, step=1, label="Soul Score", interactive=False)
            energy_out = gr.Textbox(label="Energy Level", interactive=False)
            class_out = gr.Textbox(label="Classification", interactive=False)
            verdict_out = gr.Textbox(label="Verdict", interactive=False)
            reasons_out = gr.Textbox(label="Reasons", lines=6, interactive=False)
            code_echo = gr.Code(label="Input Echo", language="python", interactive=False)

    run_btn.click(
        fn=gradio_analyze,
        inputs=[code_in],
        outputs=[score_out, energy_out, class_out, verdict_out, reasons_out, code_echo],
    )

if __name__ == "__main__":
    demo.launch()