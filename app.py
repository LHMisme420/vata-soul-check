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

    # naming / repetition
    naming_entropy: float
    repetition_ratio: float

    # token-level fingerprint
    token_entropy: float
    operator_density: float
    operator_spacing_variance: float


COMMENT_RE = re.compile(r'^\s*#')
TODO_RE = re.compile(r'\bTODO\b', re.IGNORECASE)
DEBUG_RE = re.compile(r'\bprint\(')
MAGIC_NUMBER_RE = re.compile(r'\b\d+\b')
VAR_NAME_RE = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')

TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*"  
    r"|\d+"                    
    r"|==|!=|<=|>="            
    r"|[+\-*/%=<>():,\.]"      
)

OPERATORS = set(["+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">="])

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


def extract_token_fingerprint(code: str) -> Dict[str, float]:
    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip()]
    if not non_empty:
        return {
            "token_entropy": 0.0,
            "operator_density": 0.0,
            "operator_spacing_variance": 0.0,
        }

    all_tokens: List[str] = []
    operator_spacing_samples: List[int] = []

    for line in non_empty:
        tokens = TOKEN_RE.findall(line)
        all_tokens.extend(tokens)

        for match in TOKEN_RE.finditer(line):
            tok = match.group(0)
            if tok in OPERATORS:
                start = match.start()

                left_space = 0
                right_space = 0

                i = start - 1
                while i >= 0 and line[i] == " ":
                    left_space += 1
                    i -= 1

                j = match.end()
                while j < len(line) and line[j] == " ":
                    right_space += 1
                    j += 1

                operator_spacing_samples.append(left_space + right_space)

    token_entropy = shannon_entropy(all_tokens)

    operator_density = 0.0
    if all_tokens:
        operator_density = sum(1 for t in all_tokens if t in OPERATORS) / len(all_tokens)

    operator_spacing_variance = 0.0
    if len(operator_spacing_samples) > 1:
        operator_spacing_variance = statistics.pvariance(operator_spacing_samples)

    return {
        "token_entropy": token_entropy,
        "operator_density": operator_density,
        "operator_spacing_variance": operator_spacing_variance,
    }


def extract_soul_signal(code: str) -> SoulSignal:
    lines: List[str] = code.splitlines()
    non_empty = [l for l in lines if l.strip()]
    line_count = len(non_empty) or 1

    line_lengths = [len(l) for l in non_empty]
    avg_line_length = sum(line_lengths) / line_count

    indents = [(len(l) - len(l.lstrip(" "))) for l in non_empty]
    indent_variance = statistics.pvariance(indents) if len(indents) > 1 else 0.0

    comments = [l for l in non_empty if COMMENT_RE.search(l)]
    comment_density = len(comments) / line_count

    todo_count = sum(1 for l in comments if TODO_RE.search(l))

    reasoning_comment_count = sum(
        1 for l in comments if any(h in l.lower() for h in REASONING_HINTS)
    )

    debug_artifacts = sum(1 for l in non_empty if DEBUG_RE.search(l))

    magic_numbers = sum(
        len(MAGIC_NUMBER_RE.findall(l))
        for l in non_empty
        if "for " not in l and "range(" not in l
    )

    names = [
        name
        for l in non_empty
        if not COMMENT_RE.search(l)
        for name in VAR_NAME_RE.findall(l)
        if len(name) > 1
    ]

    naming_entropy = shannon_entropy(names)

    repetition_ratio = 0.0
    if names:
        from collections import Counter
        counts = Counter(names)
        repetition_ratio = counts.most_common(1)[0][1] / len(names)

    token_fp = extract_token_fingerprint(code)

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
        token_entropy=token_fp["token_entropy"],
        operator_density=token_fp["operator_density"],
        operator_spacing_variance=token_fp["operator_spacing_variance"],
    )


# =========================
#   SCORING / CLASSIFIER
# =========================

def score_soul(signal: SoulSignal) -> Dict[str, Any]:
    reasons: List[str] = []
    human_score = 0.0

    human_score += min(signal.comment_density * 50, 25)
    if signal.todo_count > 0:
        human_score += 10
        reasons.append("TODO markers detected.")
    if signal.reasoning_comment_count > 0:
        human_score += 15
        reasons.append("Reasoning-style comments detected.")

    if signal.debug_artifacts > 0:
        human_score += 20
        reasons.append("Debug prints detected.")

    if signal.magic_numbers > 0:
        human_score += min(signal.magic_numbers * 4, 12)
        reasons.append("Magic numbers detected.")

    if signal.indent_variance > 0:
        human_score += min(signal.indent_variance * 0.5, 10)
        reasons.append("Indentation irregularity detected.")

    if signal.naming_entropy > 2.0:
        human_score += 10
        reasons.append("High naming entropy (varied identifiers).")
    elif signal.naming_entropy < 1.0 and signal.line_count > 10:
        human_score -= 5
        reasons.append("Low naming entropy (repetitive identifiers).")

    if signal.repetition_ratio > 0.5 and signal.line_count > 10:
        human_score -= 8
        reasons.append("High identifier repetition detected.")

    if signal.token_entropy > 4.0:
        human_score += 10
        reasons.append("High token entropy (varied token usage).")
    elif signal.token_entropy < 2.0 and signal.line_count > 10:
        human_score -= 5
        reasons.append("Low token entropy (regular token patterns).")

    if 0.05 <= signal.operator_density <= 0.25:
        human_score += 5
        reasons.append("Balanced operator density.")
    else:
        human_score -= 3
        reasons.append("Unusual operator density.")

    if signal.operator_spacing_variance > 0.5:
        human_score += 7
        reasons.append("Inconsistent operator spacing (human-like).")
    elif signal.operator_spacing_variance < 0.1 and signal.line_count > 10:
        human_score -= 5
        reasons.append("Highly consistent operator spacing (AI-like).")

    if signal.line_count < 5:
        human_score *= 0.7
        reasons.append("Short snippet penalty applied.")

    human_score = max(0.0, min(100.0, human_score))

    prob_human = 1 / (1 + math.exp(-(human_score - 50) / 10))
    prob_human_pct = round(prob_human * 100, 1)

    if prob_human_pct >= 75:
        classification = "LIKELY HUMAN-AUTHORED"
        verdict = "PASS"
    elif prob_human_pct >= 45:
        classification = "UNCERTAIN"
        verdict = "REVIEW"
    else:
        classification = "LIKELY AI-GENERATED"
        verdict = "FLAG"

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
#   DARK MODE UI
# =========================

EXAMPLE_CODE = """# Human-like messy code with intent
def calculate_something(x):
    # TODO: optimize this later
    # quick hack for now because deadline
    result = x * 2 + 42  # magic number from 2am debugging
    print("Debug: ", result)
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
    reasons_str = "\n".join(f"- {r}" for r in res["reasons"])
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


with gr.Blocks(
    title="VATA Authorship Fingerprint",
    theme=gr.themes.Monochrome(),
) as demo:

    gr.Markdown(
        """
        <div style='text-align:center; font-size:32px; font-weight:700; color:#E0E0E0;'>
            VATA Authorship Fingerprint
        </div>
        <div style='text-align:center; font-size:16px; color:#A0A0A0; margin-bottom:20px;'>
            Forensic analysis of code for likely human vs AI authorship.
        </div>
        """,
    )

    with gr.Row():
        with gr.Column(scale=1):
            code_in = gr.Code(
                label="Code Input",
                language="python",
                value=EXAMPLE_CODE,
            )
            run_btn = gr.Button("Analyze", variant="primary")

        with gr.Column(scale=1):
            human_score_out = gr.Slider(
                0, 100, value=0, step=1, label="Human Behavior Score", interactive=False
            )
            prob_out = gr.Slider(
                0, 100, value=0, step=0.1,
                label="Estimated Human Authorship Probability (%)",
                interactive=False,
            )
            energy_out = gr.Textbox(label="Signal Level", interactive=False)
            class_out = gr.Textbox(label="Classification", interactive=False)
            reasons_out = gr.Textbox(label="Why this result?", lines=8, interactive=False)
            raw_out = gr.Textbox(label="Raw Metrics", lines=12, interactive=False)
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