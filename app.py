import re
import math
import statistics
from dataclasses import dataclass
from typing import List, Dict, Any

import gradio as gr


# =========================
#   FEATURE + SIGNAL MODEL
# =========================

@dataclass
class SoulSignal:
    # structural / style
    line_count: int
    avg_line_length: float
    indent_variance: float

    # comments / intent
    comment_density: float
    todo_count: int
    reasoning_comment_count: int

    # artifacts / mess
    debug_artifacts: int
    magic_numbers: int

    # pattern / regularity
    naming_entropy: float
    repetition_ratio: float


COMMENT_RE = re.compile(r'^\s*#')
TODO_RE = re.compile(r'\bTODO\b', re.IGNORECASE)
DEBUG_RE = re.compile(r'\bprint\(')
MAGIC_NUMBER_RE = re.compile(r'\b\d+\b')
FUNC_DEF_RE = re.compile(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)')
VAR_NAME_RE = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')

REASONING_HINTS = [
    "because",
    "why",
    "so that",
    "workaround",
    "hack",
    "temporary",
    "for now",
    "later",
]


def shannon_entropy(tokens: List[str]) -> float:
    if not tokens:
        return 0.0
    from collections import Counter
    counts = Counter(tokens)
    total = sum(counts.values())
    ent = 0.0
    for c in counts.values():
        p = c / total
        ent -= p * math.log2(p)
    return ent


def extract_soul_signal(code: str) -> SoulSignal:
    lines: List[str] = code.splitlines()
    non_empty = [l for l in lines if l.strip()]
    line_count = len(non_empty) or 1

    # line length + indentation
    line_lengths = [len(l) for l in non_empty]
    avg_line_length = sum(line_lengths) / line_count

    indents = []
    for l in non_empty:
        leading_spaces = len(l) - len(l.lstrip(" "))
        indents.append(leading_spaces)
    indent_variance = statistics.pvariance(indents) if len(indents) > 1 else 0.0

    # comments + TODO + reasoning comments
    comments = [l for l in non_empty if COMMENT_RE.search(l)]
    comment_density = len(comments) / line_count

    todo_count = sum(1 for l in comments if TODO_RE.search(l))

    reasoning_comment_count = 0
    for l in comments:
        lower = l.lower()
        if any(h in lower for h in REASONING_HINTS):
            reasoning_comment_count += 1

    # debug artifacts
    debug_artifacts = sum(1 for l in non_empty if DEBUG_RE.search(l))

    # magic numbers (excluding obvious loop constructs)
    magic_numbers = 0
    for l in non_empty:
        if "for " in l or "range(" in l:
            continue
        magic_numbers += len(MAGIC_NUMBER_RE.findall(l))

    # naming entropy + repetition
    names: List[str] = []
    for l in non_empty:
        # skip comments
        if COMMENT_RE.search(l):
            continue
        for name in VAR_NAME_RE.findall(l):
            # filter out keywords-ish / builtins-ish by crude length/shape
            if len(name) <= 1:
                continue
            names.append(name)

    naming_entropy = shannon_entropy(names)

    repetition_ratio = 0.0
    if names:
        from collections import Counter
        counts = Counter(names)
        most_common = counts.most_common(1)[0][1]
        repetition_ratio = most_common / len(names)

    return SoulSignal(
        line_count=line_count,
        avg_line_length=avg_line_length,
        indent_variance=indent_variance,
        comment_density=comment_density,
        todo_count=todo_count,
        reasoning_comment_count=reasoning_comment_count,
        debug_artifacts=debug_artifacts,
        magic_numbers=magic_numbers,
        naming_entropy=naming_entropy,
        repetition_ratio=repetition_ratio,
    )


# =========================
#   SCORING / CLASSIFIER
# =========================

def score_soul(signal: SoulSignal) -> Dict[str, Any]:
    reasons: List[str] = []

    # Start with a neutral base
    human_score = 0.0

    # 1) Comments + TODOs + reasoning
    human_score += min(signal.comment_density * 50, 25)
    if signal.todo_count > 0:
        human_score += 10
        reasons.append("Found TODO markers (future-intent / planning).")
    if signal.reasoning_comment_count > 0:
        human_score += 15
        reasons.append("Found reasoning-style comments (explaining why, not just what).")

    # 2) Debug artifacts
    if signal.debug_artifacts > 0:
        human_score += 20
        reasons.append("Found debug prints (live debugging traces).")

    # 3) Magic numbers
    if signal.magic_numbers > 0:
        human_score += min(signal.magic_numbers * 4, 12)
        reasons.append("Found magic numbers (non-parameterized constants).")

    # 4) Structural irregularity (indent variance)
    if signal.indent_variance > 0:
        human_score += min(signal.indent_variance * 0.5, 10)
        reasons.append("Non-uniform indentation (human-style structural variation).")

    # 5) Naming entropy + repetition
    # Higher entropy = more varied naming (human-like)
    # High repetition ratio = same names reused everywhere (more synthetic)
    if signal.naming_entropy > 2.0:
        human_score += 10
        reasons.append("High naming entropy (varied identifiers, human-like).")
    elif signal.naming_entropy < 1.0 and signal.line_count > 10:
        human_score -= 5
        reasons.append("Low naming entropy (overly repetitive identifiers).")

    if signal.repetition_ratio > 0.5 and signal.line_count > 10:
        human_score -= 8
        reasons.append("High identifier repetition (patterned, synthetic-like).")

    # 6) Size bias: very short snippets are ambiguous
    if signal.line_count < 5:
        human_score *= 0.7
        reasons.append("Very short snippet (authorship harder to infer).")

    # Clamp to [0, 100]
    human_score = max(0.0, min(100.0, human_score))

    # Convert to probability-like value via a simple logistic
    # (not trained, but shaped to feel like a probability)
    prob_human = 1 / (1 + math.exp(-(human_score - 50) / 10))
    prob_human_pct = round(prob_human * 100, 1)

    # Classification
    if prob_human_pct >= 75:
        classification = "LIKELY HUMAN-AUTHORED"
        verdict = "VATA COMPLIANT"
    elif prob_human_pct >= 45:
        classification = "UNCERTAIN"
        verdict = "REQUIRES REVIEW"
    else:
        classification = "LIKELY AI-GENERATED"
        verdict = "VATA FLAGGED"

    # Energy label (kept for your theme, but grounded in score)
    if human_score >= 80:
        energy_level = "High Human Signal"
    elif human_score >= 50:
        energy_level = "Mixed Signal"
    else:
        energy_level = "Low Human Signal"

    return {
        "human_score": round(human_score, 1),
        "prob_human_pct": prob_human_pct,
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

EXAMPLE_CODE = """# Human-like messy code with intent
def calculate_something(x):
    # TODO: optimize this later
    # quick hack for now because deadline
    result = x * 2 + 42  # magic number from 2am debugging
    print("Debug: ", result)  # left over debug print
    return result
"""


def gradio_analyze(code: str):
    if not code.strip():
        return (
            0,
            0.0,
            "Low Human Signal",
            "N/A",
            "No code provided.",
            "{}",
            "",
        )
    res = analyze_code(code)
    reasons_str = "\n".join(f"- {r}" for r in res["reasons"]) or "No specific reasons detected."
    raw_signal_str = "\n".join(f"{k}: {v}" for k, v in res["raw_signal"].items())
    return (
        res["human_score"],
        res["prob_human_pct"],
        res["energy_level"],
        res["classification"],
        reasons_str,
        raw_signal_str,
        res["input_code"],
    )


with gr.Blocks(title="VATA Soul Check") as demo:
    gr.Markdown(
        "# VATA Soul Check\n"
        "Behavior-based analysis of code for likely human vs AI authorship.\n"
        "_Scores are heuristic and explainable, not mystical._"
    )

    with gr.Row():
        with gr.Column():
            code_in = gr.Code(
                label="Code Input",
                language="python",
                value=EXAMPLE_CODE,
            )
            run_btn = gr.Button("Analyze")

        with gr.Column():
            human_score_out = gr.Slider(
                0, 100, value=0, step=1, label="Human Behavior Score", interactive=False
            )
            prob_out = gr.Slider(
                0, 100, value=0, step=0.1, label="Estimated Human Authorship Probability (%)", interactive=False
            )
            energy_out = gr.Textbox(label="Signal Level", interactive=False)
            class_out = gr.Textbox(label="Classification", interactive=False)
            reasons_out = gr.Textbox(label="Why this result?", lines=8, interactive=False)
            raw_out = gr.Textbox(label="Raw Metrics", lines=10, interactive=False)
            code_echo = gr.Code(label="Input Echo", language="python", interactive=False)

    run_btn.click(
        fn=gradio_analyze,
        inputs=[code_in],
        outputs=[
            human_score_out,
            prob_out,
            energy_out,
            class_out,
            reasons_out,
            raw_out,
            code_echo,
        ],
    )

if __name__ == "__main__":
    demo.launch()