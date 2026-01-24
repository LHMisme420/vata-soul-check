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
class Fingerprint:
    line_count: int
    avg_line_length: float
    indent_variance: float
    comment_density: float
    todo_count: int
    reasoning_comment_count: int
    debug_artifacts: int
    magic_numbers: int
    naming_entropy: float
    repetition_ratio: float
    token_entropy: float
    operator_density: float
    operator_spacing_variance: float


COMMENT_RE = re.compile(r'^\s*#')
TODO_RE = re.compile(r'\bTODO\b', re.IGNORECASE)
DEBUG_RE = re.compile(r'\bprint\(')
MAGIC_NUMBER_RE = re.compile(r'\b\d+\b')
VAR_NAME_RE = re.compile(r'\b([a-zA-Z_][A-Za-z0-9_]*)\b')

TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*"
    r"|\d+"
    r"|==|!=|<=|>="
    r"|[+\-*/%=<>():,\.]"
)

OPERATORS = {"+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">="}

REASONING_HINTS = [
    "because", "why", "so that", "workaround",
    "hack", "temporary", "for now", "later"
]


def entropy(tokens: List[str]) -> float:
    if not tokens:
        return 0.0
    from collections import Counter
    counts = Counter(tokens)
    total = sum(counts.values())
    return -sum((c/total) * math.log2(c/total) for c in counts.values())


# =========================
#   FEATURE EXTRACTION
# =========================

def extract_fingerprint(code: str) -> Fingerprint:
    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip()]
    line_count = len(non_empty) or 1

    # structural
    lengths = [len(l) for l in non_empty]
    avg_line_length = sum(lengths) / line_count

    indents = [(len(l) - len(l.lstrip(" "))) for l in non_empty]
    indent_variance = statistics.pvariance(indents) if len(indents) > 1 else 0.0

    # comments
    comments = [l for l in non_empty if COMMENT_RE.search(l)]
    comment_density = len(comments) / line_count
    todo_count = sum(1 for l in comments if TODO_RE.search(l))
    reasoning_comment_count = sum(
        1 for l in comments if any(h in l.lower() for h in REASONING_HINTS)
    )

    # artifacts
    debug_artifacts = sum(1 for l in non_empty if DEBUG_RE.search(l))
    magic_numbers = sum(
        len(MAGIC_NUMBER_RE.findall(l))
        for l in non_empty
        if "for " not in l and "range(" not in l
    )

    # naming entropy
    names = [
        n for l in non_empty
        if not COMMENT_RE.search(l)
        for n in VAR_NAME_RE.findall(l)
        if len(n) > 1
    ]
    naming_entropy = entropy(names)

    repetition_ratio = 0.0
    if names:
        from collections import Counter
        counts = Counter(names)
        repetition_ratio = counts.most_common(1)[0][1] / len(names)

    # token fingerprint
    all_tokens = []
    operator_spacing = []

    for line in non_empty:
        tokens = TOKEN_RE.findall(line)
        all_tokens.extend(tokens)

        for match in TOKEN_RE.finditer(line):
            tok = match.group(0)
            if tok in OPERATORS:
                start = match.start()

                left = 0
                right = 0

                i = start - 1
                while i >= 0 and line[i] == " ":
                    left += 1
                    i -= 1

                j = match.end()
                while j < len(line) and line[j] == " ":
                    right += 1
                    j += 1

                operator_spacing.append(left + right)

    token_entropy = entropy(all_tokens)
    operator_density = (
        sum(1 for t in all_tokens if t in OPERATORS) / len(all_tokens)
        if all_tokens else 0.0
    )
    operator_spacing_variance = (
        statistics.pvariance(operator_spacing)
        if len(operator_spacing) > 1 else 0.0
    )

    return Fingerprint(
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
        token_entropy=token_entropy,
        operator_density=operator_density,
        operator_spacing_variance=operator_spacing_variance,
    )


# =========================
#   SCORING ENGINE
# =========================

def score(f: Fingerprint) -> Dict[str, Any]:
    reasons = []
    score = 0.0

    # comment signals
    score += min(f.comment_density * 50, 25)
    if f.todo_count:
        score += 10
        reasons.append("TODO markers detected.")
    if f.reasoning_comment_count:
        score += 15
        reasons.append("Reasoning-style comments detected.")

    # artifacts
    if f.debug_artifacts:
        score += 20
        reasons.append("Debug prints detected.")
    if f.magic_numbers:
        score += min(f.magic_numbers * 4, 12)
        reasons.append("Magic numbers detected.")

    # structure
    if f.indent_variance > 0:
        score += min(f.indent_variance * 0.5, 10)
        reasons.append("Indentation irregularity detected.")

    # naming
    if f.naming_entropy > 2.0:
        score += 10
        reasons.append("High naming entropy.")
    elif f.naming_entropy < 1.0 and f.line_count > 10:
        score -= 5
        reasons.append("Low naming entropy.")

    if f.repetition_ratio > 0.5 and f.line_count > 10:
        score -= 8
        reasons.append("High identifier repetition.")

    # token-level
    if f.token_entropy > 4.0:
        score += 10
        reasons.append("High token entropy.")
    elif f.token_entropy < 2.0 and f.line_count > 10:
        score -= 5
        reasons.append("Low token entropy.")

    if 0.05 <= f.operator_density <= 0.25:
        score += 5
    else:
        score -= 3

    if f.operator_spacing_variance > 0.5:
        score += 7
    elif f.operator_spacing_variance < 0.1 and f.line_count > 10:
        score -= 5

    # short snippet penalty
    if f.line_count < 5:
        score *= 0.7

    score = max(0, min(100, score))
    prob = round(1 / (1 + math.exp(-(score - 50) / 10)) * 100, 1)

    if prob >= 75:
        classification = "LIKELY HUMAN"
    elif prob >= 45:
        classification = "UNCERTAIN"
    else:
        classification = "LIKELY AI"

    return {
        "score": score,
        "probability": prob,
        "classification": classification,
        "reasons": reasons,
        "raw": f.__dict__,
    }


# =========================
#   UI
# =========================

EXAMPLE = """# Human-like messy code
def calc(x):
    # TODO: fix later
    result = x * 2 + 42
    print("debug:", result)
    return result
"""


def run(code: str):
    if not code.strip():
        return 0, 0, "N/A", "No code provided.", "{}", ""

    fp = extract_fingerprint(code)
    res = score(fp)

    reasons = "\n".join(f"- {r}" for r in res["reasons"])
    raw = "\n".join(f"{k}: {v}" for k, v in res["raw"].items())

    return (
        res["score"],
        res["probability"],
        res["classification"],
        reasons,
        raw,
        code,
    )


with gr.Blocks(theme=gr.themes.Monochrome()) as demo:
    gr.Markdown(
        "<h1 style='text-align:center;color:#E0E0E0;'>VATA Authorship Fingerprint</h1>"
        "<p style='text-align:center;color:#A0A0A0;'>Forensic analysis of human vs AI code behavior.</p>"
    )

    with gr.Row():
        with gr.Column():
            code_in = gr.Code(label="Code Input", value=EXAMPLE, language="python")
            btn = gr.Button("Analyze", variant="primary")

        with gr.Column():
            score_out = gr.Slider(0, 100, label="Human Behavior Score", interactive=False)
            prob_out = gr.Slider(0, 100, label="Human Authorship Probability (%)", interactive=False)
            class_out = gr.Textbox(label="Classification", interactive=False)
            reasons_out = gr.Textbox(label="Reasons", lines=8, interactive=False)
            raw_out = gr.Textbox(label="Raw Metrics", lines=12, interactive=False)
            echo = gr.Code(label="Input Echo", language="python", interactive=False)

    btn.click(run, code_in, [score_out, prob_out, class_out, reasons_out, raw_out, echo])


if __name__ == "__main__":
    demo.launch()