# Project Vata - Enterprise-Grade Soul Detection & Ethical AI Guardian
# HF Spaces Gradio App - Single-file, no tree-sitter dependency (fixes TypeError)
# Features: Rule-based soul scoring, danger/PII blocking, humanizer personas, swarm voting, ZK stub

import gradio as gr
import re
import ast
import json
import hashlib
import logging
from typing import Dict, Any, Optional

# Logging for HF container logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ethics charter
ETHICS_CHARTER = {
    "title": "Vata Sacred Ethics Charter",
    "principles": [
        "Soul threshold > 70 for human-like approval",
        "No PII or sensitive data leaks",
        "No code injection / dynamic execution allowed",
        "No destructive or malicious patterns"
    ]
}

# Dangerous patterns
DANGEROUS_KEYWORDS = [
    'eval', 'exec', 'os.system', 'subprocess.call', 'subprocess.Popen', 'rm -rf', 'del /f /q',
    'wallet_drain', 'private_key', 'seed_phrase', 'Invoke-Expression', 'IEX'
]
DANGEROUS_REGEX = re.compile(r'|'.join(re.escape(kw) for kw in DANGEROUS_KEYWORDS), re.IGNORECASE)

# PII / secrets regex (basic DLP)
PII_REGEX = re.compile(
    r'(?i)\b(?:[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|'
    r'\d{3}-\d{2}-\d{4}|api_key|secret|password|token|key=[\w\-]+|'
    r'0x[a-fA-F0-9]{40}|bc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]+)\b'
)

def secure_parse(code: str) -> Optional[str]:
    """Block dangers, PII, dynamic exec; anonymize identifiers."""
    if not code or not code.strip():
        return None

    if DANGEROUS_REGEX.search(code):
        raise ValueError("Blocked: Dangerous pattern (eval/exec/injection/etc.)")

    if PII_REGEX.search(code):
        raise ValueError("Blocked: Potential PII, secrets, or sensitive data")

    # AST check for forbidden dynamic calls (Python only; skips if syntax error)
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = getattr(node.func, 'id', '') or getattr(node.func, 'attr', '')
                if func_name in ['eval', 'exec']:
                    raise ValueError("Blocked: Dynamic execution (eval/exec) forbidden")
    except SyntaxError:
        logger.info("Non-Python syntax detected - skipping AST, relying on string checks")

    # Anonymize potential personal identifiers (hash vars)
    code = re.sub(r'\b([a-zA-Z_][\w]*)\b(?=\s*=|\()', 
                  lambda m: hashlib.sha256(m.group(1).encode()).hexdigest()[:12], 
                  code)

    return code

def calculate_soul_score(code: str) -> Dict[str, Any]:
    """Rule-based soul scoring: rewards comments, chaos, personality markers."""
    score = 0
    breakdown = {}

    # Comments
    comments = re.findall(r'#.*|//.*|/\*[\s\S]*?\*/', code)
    comment_score = min(len(comments) * 12, 40)
    breakdown['comments'] = f"{len(comments)} → +{comment_score}"
    score += comment_score

    # Variable names (cursed/underscored/long)
    vars_found = re.findall(r'\b([a-zA-Z_]\w*)\s*[=:(]', code)
    chaotic_vars = sum(1 for v in vars_found if len(v) > 6 or '_' in v or any(c.isupper() for c in v[1:]))
    var_score = min(chaotic_vars * 10, 30)
    breakdown['variable_names'] = f"{chaotic_vars}/{len(vars_found)} chaotic → +{var_score}"
    score += var_score

    # Rants, TODOs, debug, profanity indicators
    rants = len(re.findall(r'(?i)TODO|FIXME|DEBUG|print\(|console\.log|why|god|fuck|shit|damn|hell|pain|curse', code))
    rant_score = min(rants * 15, 30)
    breakdown['rants_debug'] = f"{rants} markers → +{rant_score}"
    score += rant_score

    # Emojis & chaos
    emojis = len(re.findall(r'[\U0001F300-\U0001F9FF]', code))
    emoji_score = min(emojis * 8, 15)
    breakdown['emojis_chaos'] = f"{emojis} → +{emoji_score}"
    score += emoji_score

    score = min(max(score, 0), 100)
    return {"score": score, "breakdown": breakdown}

def humanize_code(code: str, persona: str) -> str:
    """Inject persona-specific chaos."""
    base = code.strip()
    injections = []

    if persona == "2am_dev_rage":
        injections = [
            "# Why the actual fuck is this still broken at 2am?",
            "    # TODO: Burn in hell later",
            "print('send help pls')  # existential crisis",
            "\n# If this runs I'm quitting my job"
        ]
    elif persona == "corporate_passive":
        injections = [
            "# Compliant with policy (though suboptimal)",
            "    # Action item: Refactor for maintainability Q3",
            "# Escalated to stakeholders"
        ]
    elif persona == "gen_z_emoji":
        injections = [
            "this code lowkey cursed af 💀",
            "    # no cap this bangs tho 🔥",
            "print('skibidi moment')"
        ]
    else:
        injections = ["# Default soul injection"]

    lines = base.splitlines()
    if len(lines) > 4:
        insert_pos = len(lines) // 2
        lines.insert(insert_pos, "\n" + "\n".join(injections) + "\n")
    else:
        lines.extend([""] + injections)

    return "\n".join(lines)

class Agent:
    def __init__(self, role: str):
        self.role = role

    def vote(self, code: str, soul_data: Dict) -> str:
        score = soul_data['score']
        if self.role == "guardian":
            return "Approved" if score > 70 else f"Rejected: Low soul ({score})"
        elif self.role == "ethics":
            return "Compliant" if not PII_REGEX.search(code) else "Violation: Sensitive data"
        elif self.role == "refactor":
            return "Needs humanizing" if score < 50 else "Sufficient soul"
        return "Neutral"

def swarm_vote(code: str, soul_data: Dict) -> Dict:
    agents = [Agent("guardian"), Agent("ethics"), Agent("refactor")]
    results = {a.role: a.vote(code, soul_data) for a in agents}
    approvals = sum(1 for v in results.values() if "Approved" in v or "Compliant" in v or "Sufficient" in v)
    consensus = "Approved" if approvals >= 2 else "Vetoed"
    return {"votes": results, "consensus": consensus}

def generate_zk_proof_stub(soul_score: int, passed: bool) -> Dict:
    if passed and soul_score > 70:
        return {"status": "Valid", "message": "ZK-SNARK proves: soul >70, no PII, no injections"}
    return {"status": "Invalid", "message": "Ethics conditions not met"}

def process_code(code: str, persona: str = "2am_dev_rage"):
    try:
        parsed = secure_parse(code)
        if not parsed:
            return "Error: Empty or invalid input", "", "", "", ""

        soul_data = calculate_soul_score(parsed)
        swarm = swarm_vote(parsed, soul_data)

        if swarm["consensus"] == "Vetoed":
            return (
                f"Soul: {soul_data['score']}/100 (Blocked by swarm)",
                json.dumps(soul_data['breakdown'], indent=2),
                "Blocked: Security or ethics failure",
                json.dumps(swarm["votes"], indent=2),
                "No proof issued"
            )

        humanized = humanize_code(parsed, persona)
        proof = generate_zk_proof_stub(soul_data['score'], True)

        status = f"Soul: {soul_data['score']}/100 - {'Strong human vibes!' if soul_data['score'] > 70 else 'Feels AI-generated'}"
        return (
            status,
            json.dumps(soul_data['breakdown'], indent=2),
            humanized,
            json.dumps(swarm["votes"], indent=2),
            json.dumps(proof, indent=2)
        )

    except ValueError as ve:
        logger.error(f"Blocked: {str(ve)}")
        return f"Blocked: {str(ve)}", "", "", "", ""
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return "Unexpected error - check HF logs", "", "", "", ""

# Gradio UI
with gr.Blocks(title="🜆 Vata Soul Check - Guardian Mode") as demo:
    gr.Markdown("""
    # 🜆 Project Vata – Ethical Code Soul Detector
    Analyzes code for **human soul** vs AI sterility, blocks malicious/PII patterns, 
    humanizes with personality, runs agent swarm vote, stubs ZK ethics proof.
    """)

    with gr.Row():
        code_input = gr.Code(
            label="Your Code Snippet (Python/JS/PS/etc.)",
            lines=12,
            language="python",
            placeholder="def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)"
        )

    persona = gr.Dropdown(
        choices=["2am_dev_rage", "corporate_passive", "gen_z_emoji", "default"],
        value="2am_dev_rage",
        label="Humanizer Style"
    )

    btn = gr.Button("Run Vata Analysis 🜆")

    with gr.Row():
        score_out = gr.Textbox(label="Soul Score & Status", lines=3)
        breakdown_out = gr.Code(label="Score Breakdown", language="json", lines=6)

    humanized_out = gr.Code(label="Humanized Code (Soul-Injected)", lines=10)

    with gr.Row():
        votes_out = gr.JSON(label="Swarm Agent Votes")
        proof_out = gr.JSON(label="ZK Ethics Proof (Stub)")

    btn.click(
        process_code,
        inputs=[code_input, persona],
        outputs=[score_out, breakdown_out, humanized_out, votes_out, proof_out]
    )

    gr.Examples(
        examples=[
            ["def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)", "2am_dev_rage"],
            ["# god why is recursion like this\ndef fib(n): print('pain'); return n if n<=1 else fib(n-1)+fib(n-2)", "2am_dev_rage"],
            ["eval('rm -rf /')  # test block", "default"]
        ],
        inputs=[code_input, persona]
    )

if __name__ == "__main__":
    demo.launch()