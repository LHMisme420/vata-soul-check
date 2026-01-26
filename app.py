# Project Vata - Ethical Code Soul Detector & Humanizer
# Single-file Gradio app for Hugging Face Spaces
# Fixed version: removed invalid 'placeholder', added visual score, extra persona

import gradio as gr
import re
import ast
import json
import hashlib
import logging
from typing import Dict, Any, Optional

# Logging (visible in HF container logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dangerous patterns
DANGEROUS_REGEX = re.compile(
    r'(?i)eval|exec|os\.system|subprocess|rm -rf|del /f /q|'
    r'wallet_drain|private_key|seed_phrase|Invoke-Expression|IEX'
)

PII_REGEX = re.compile(
    r'(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|\d{3}-\d{2}-\d{4}|'
    r'api_key|secret|password|token|key=[\w\-]+|0x[a-fA-F0-9]{40}|'
    r'bc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]+'
)

def secure_parse(code: str) -> Optional[str]:
    if not code.strip():
        return None

    if DANGEROUS_REGEX.search(code):
        raise ValueError("Dangerous pattern detected (eval/exec/os.system/subprocess/rm -rf/etc.)")

    if PII_REGEX.search(code):
        raise ValueError("Potential sensitive information detected (email, key, password, wallet, etc.)")

    # Basic Python AST check for dangerous dynamic execution
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, 'id', '') or getattr(node.func, 'attr', '')
                if name in {'eval', 'exec'}:
                    raise ValueError("Dynamic code execution (eval/exec) is not allowed")
    except SyntaxError:
        pass  # non-Python code → skip AST

    # Simple anonymization of identifiers
    code = re.sub(r'\b([a-zA-Z_]\w*)\b(?=\s*=|\()', 
                  lambda m: hashlib.sha256(m.group(1).encode()).hexdigest()[:12], 
                  code)

    return code

def calculate_soul_score(code: str) -> Dict[str, Any]:
    score = 0
    breakdown = {}

    # Comments
    comments = len(re.findall(r'#.*|//.*|/\*[\s\S]*?\*/', code))
    comment_score = min(comments * 12, 40)
    breakdown["comments"] = f"{comments} → +{comment_score}"
    score += comment_score

    # Chaotic / human-like variable names
    vars_found = re.findall(r'\b([a-zA-Z_]\w*)\s*[=:(]', code)
    chaotic_vars = sum(1 for v in vars_found if len(v) > 6 or '_' in v or any(c.isupper() for c in v[1:]))
    var_score = min(chaotic_vars * 10, 30)
    breakdown["variable_names"] = f"{chaotic_vars}/{len(vars_found)} chaotic → +{var_score}"
    score += var_score

    # Rants, debug, TODOs, emotional markers
    rants = len(re.findall(r'(?i)TODO|FIXME|DEBUG|print\(|console\.log|why|god|fuck|shit|damn|hell|pain|curse|wtf|pls|help', code))
    rant_score = min(rants * 15, 30)
    breakdown["rants_debug"] = f"{rants} markers → +{rant_score}"
    score += rant_score

    # Emojis
    emojis = len(re.findall(r'[\U0001F300-\U0001F9FF]', code))
    emoji_score = min(emojis * 8, 15)
    breakdown["emojis"] = f"{emojis} → +{emoji_score}"
    score += emoji_score

    score = min(max(score, 0), 100)
    return {"score": score, "breakdown": breakdown}

def humanize_code(code: str, persona: str) -> str:
    base = code.strip()
    injections = []

    if persona == "2am_dev_rage":
        injections = [
            "# why the fuck is this still broken at 2:47am",
            "    # TODO: set on fire later",
            "print('kill me now')  # actual mood",
            "\n# if this works first try I become a monk"
        ]
    elif persona == "corporate_passive":
        injections = [
            "# Compliant per current policy framework",
            "    # Known technical debt – backlog item created",
            "# Stakeholders aligned (with reservations)"
        ]
    elif persona == "gen_z_emoji":
        injections = [
            "this code is actually cursed fr 💀",
            "    # no cap this kinda slaps tho 🔥",
            "print('skibidi toilet arc')"
        ]
    elif persona == "old_school_hacker":
        injections = [
            "# 0ld sk00l 31337 h4x0r style",
            "    # ph34r th3 b33r + c0d3 c0mb0",
            "printf('leet hax incoming'); // old ways die hard"
        ]
    else:
        injections = ["# added some human spice"]

    lines = base.splitlines()
    if len(lines) > 4:
        pos = len(lines) // 2
        lines.insert(pos, "\n" + "\n".join(injections) + "\n")
    else:
        lines.extend([""] + injections)

    return "\n".join(lines)

class Agent:
    def __init__(self, role: str):
        self.role = role

    def vote(self, soul_score: int, code: str) -> str:
        if self.role == "guardian":
            return "APPROVED" if soul_score > 70 else f"REJECTED (soul {soul_score})"
        if self.role == "ethics":
            return "COMPLIANT" if not PII_REGEX.search(code) else "PII / SECRETS VIOLATION"
        if self.role == "refactor":
            return "NEEDS HUMANIZING" if soul_score < 50 else "GOOD ENOUGH"
        return "NEUTRAL"

def swarm_vote(code: str, soul_data: Dict) -> Dict:
    agents = [Agent("guardian"), Agent("ethics"), Agent("refactor")]
    results = {a.role: a.vote(soul_data["score"], code) for a in agents}
    approvals = sum(1 for v in results.values() if v in {"APPROVED", "COMPLIANT", "GOOD ENOUGH"})
    consensus = "APPROVED" if approvals >= 2 else "VETOED"
    return {"votes": results, "consensus": consensus}

def format_score_visual(score: int) -> str:
    bar = "█" * (score // 10) + "░" * (10 - score // 10)
    color = "green" if score > 70 else "orange" if score >= 40 else "red"
    return f"<span style='color:{color}; font-weight:bold; font-size:1.3em'>{score}/100</span>  {bar}"

def process_code(code: str, persona: str = "2am_dev_rage"):
    try:
        parsed = secure_parse(code)
        if not parsed:
            return "No valid code provided", "", "", "", ""

        soul = calculate_soul_score(parsed)
        swarm = swarm_vote(parsed, soul)

        if swarm["consensus"] == "VETOED":
            reason = next((v for v in swarm["votes"].values() if "REJECTED" in v or "VIOLATION" in v), "Swarm veto")
            return (
                f"**BLOCKED** – {reason}",
                json.dumps(soul["breakdown"], indent=2),
                "Blocked due to security / ethics check failure",
                json.dumps(swarm["votes"], indent=2),
                "No proof generated"
            )

        humanized = humanize_code(parsed, persona)

        return (
            format_score_visual(soul["score"]),
            json.dumps(soul["breakdown"], indent=2),
            humanized,
            json.dumps(swarm["votes"], indent=2),
            "Ethics stub: soul > 70, no PII, no injection"
        )

    except ValueError as e:
        return f"**BLOCKED**: {str(e)}", "", "", "", ""
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Internal error – check space logs", "", "", "", ""

# ────────────────────────────────────────────────
#               Gradio Interface
# ────────────────────────────────────────────────

with gr.Blocks(title="🜆 Vata – Code Soul Checker") as demo:
    gr.Markdown("""
    # 🜆 Vata – Code Soul Detector & Humanizer

    Detects if code feels **human-written** (high soul) or **AI-generated slop** (low soul).  
    Blocks dangerous patterns & sensitive data.  
    Injects personality so your code looks lived-in.
    """)

    gr.Markdown("Paste code below (Python, JS, PowerShell, etc. accepted)")

    code_input = gr.Code(
        label="Your Code",
        lines=12,
        language="python",
        value="# Example – low soul\n"
              "def fib(n):\n"
              "    if n <= 1:\n"
              "        return n\n"
              "    return fib(n-1) + fib(n-2)"
    )

    persona = gr.Dropdown(
        label="Humanizer Style",
        choices=["2am_dev_rage", "corporate_passive", "gen_z_emoji", "old_school_hacker", "default"],
        value="2am_dev_rage"
    )

    btn = gr.Button("Analyze →", variant="primary", scale=0)

    gr.Markdown("Results ↓")

    with gr.Row():
        score_out = gr.Markdown(label="Soul Score", value="Waiting...")
        breakdown_out = gr.Code(label="Breakdown (why this score?)", language="json", lines=6)

    humanized_out = gr.Code(label="Humanized Version", lines=10)

    with gr.Row():
        votes_out = gr.JSON(label="Swarm Votes")
        proof_out = gr.Markdown(label="Ethics Check (stub)")

    btn.click(
        fn=process_code,
        inputs=[code_input, persona],
        outputs=[score_out, breakdown_out, humanized_out, votes_out, proof_out]
    )

    gr.Examples(
        examples=[
            ["def clean_fib(n): return n if n<=1 else clean_fib(n-1)+clean_fib(n-2)", "default"],
            ["# god why recursion hurts\nprint('pain'); def fib(n): return n if n<=1 else fib(n-1)+fib(n-2)", "2am_dev_rage"],
            ["eval('rm -rf /') # test block", "default"]
        ],
        inputs=[code_input, persona],
        label="Quick test examples"
    )

if __name__ == "__main__":
    demo.launch()