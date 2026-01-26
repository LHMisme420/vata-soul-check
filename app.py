# app.py - VATA Soul Check & Humanizer with ZK Ethics Proof
# Updated: Robust error handling for JSON parse failures + empty inputs
# Leroy H. Mason (@Lhmisme) - #ProjectVata

import gradio as gr
import json
import random
import re
from datetime import datetime

# Dummy imports - replace with your real ones
# e.g. from souldetector import detect_soul_score
# from humanizer import humanize_code
# from zk_prover import generate_zk_proof  # your ZK tease

# ======================
# HELPER FUNCTIONS
# ======================

def safe_json_loads(raw_str, fallback=None):
    """Safe JSON parse with fallback on failure/empty"""
    if not raw_str or raw_str.isspace():
        return fallback or {"error": "Empty or whitespace response", "guardian": "REJECTED (empty backend)"}
    try:
        return json.loads(raw_str)
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON: {str(e)}",
            "raw": raw_str[:300],
            "guardian": "REJECTED (parse error)"
        }
    except Exception as e:
        return {"error": str(e), "guardian": "REJECTED (unexpected)"}

def dummy_soul_detection(code):
    """Placeholder - replace with your real soul detector logic"""
    # Example heuristic: high soul = lots of comments, rants, emojis, chaos
    comment_count = len(re.findall(r'#.*', code)) + len(re.findall(r'//.*', code))
    rant_score = len(re.findall(r'(?i)(why|god|pain|help|rage|coffee|dread|fuck|shit|damn)', code))
    soul = min(100, 30 + comment_count * 8 + rant_score * 10 + random.randint(-5, 15))
    return int(soul)

def dummy_breakdown(code, soul_score):
    """Placeholder guardian/ethics breakdown"""
    if soul_score < 40:
        status = "REJECTED"
        reason = f"soul {soul_score} - too clean/soulless/obfuscated"
    elif soul_score < 70:
        status = "SUSPICIOUS"
        reason = f"soul {soul_score} - needs more chaos/personality"
    else:
        status = "APPROVED"
        reason = f"Full Soul 🔥 S+ Trusted Artisan ({soul_score})"

    return {
        "guardian": status,
        "soul_score": soul_score,
        "comments": "Detected rants, TODOs, emojis, human pain",
        "variable_names": "chaotic + self-aware",
        "ethics": "COMPLIANT" if soul_score > 50 else "QUESTIONABLE",
        "refactor": "NEEDS HUMANIZING" if soul_score < 60 else "ARTISAN LEVEL",
        "why": reason
    }

def dummy_humanize(code, style):
    """Placeholder humanizer"""
    if "rage" in style.lower():
        return code + "\n# 2am rage intensified - added extra pain"
    return code + "\n# Humanized: added personality & TODOs"

def dummy_zk_proof():
    """Tease ZK proof"""
    return "ZK-SNARK proof generated (vPoC) - ethics compliant (hash: deadbeef123)"

# ======================
# MAIN PREDICT FUNCTION
# ======================

def analyze_code(code, humanizer_style):
    """
    Gradio predict fn - always return 3-4 outputs in same order:
    1. breakdown_dict (for JSON display)
    2. humanized_code (str)
    3. zk_proof (str)
    4. status_message (str) - optional
    """
    try:
        code = (code or "").strip()
        if not code:
            error_dict = {
                "guardian": "REJECTED (no input)",
                "error": "Paste real code (Python/JS/PS/etc.)"
            }
            return error_dict, "Blocked: no code", "No proof", "Empty input"

        # === Your real soul check here ===
        soul_score = dummy_soul_detection(code)  # REPLACE with real call

        # === Guardian/breakdown ===
        breakdown_raw = dummy_breakdown(code, soul_score)  # REPLACE if LLM-based
        breakdown = safe_json_loads(json.dumps(breakdown_raw), breakdown_raw)  # ensure dict

        # === Humanized version ===
        if soul_score < 30:  # example block threshold
            humanized = "Blocked due to security / ethics check failure"
        else:
            humanized = dummy_humanize(code, humanizer_style)  # REPLACE

        # === ZK proof ===
        proof = dummy_zk_proof() if soul_score >= 70 else "No proof generated - low soul"

        # Swarm votes example (placeholder)
        swarm = {
            "guardian": breakdown.get("guardian", "UNKNOWN"),
            "ethics": breakdown.get("ethics", "N/A"),
            "refactor": breakdown.get("refactor", "N/A")
        }

        status_msg = f"Analyzed - Soul {soul_score} | {breakdown.get('guardian')}"

        return breakdown, humanized, proof, status_msg

    except Exception as e:
        error_dict = {
            "guardian": "REJECTED (crash)",
            "error": str(e),
            "trace": "Check HF Logs for details"
        }
        return error_dict, "Blocked: internal error", "No proof", f"Error: {str(e)[:100]}"

# ======================
# GRADIO INTERFACE
# ======================

with gr.Blocks(title="VATA Soul Check & Humanizer") as demo:
    gr.Markdown(
        """
        # VATA - Code Soul Detector, Humanizer & ZKP Ethics Prover
        Detects human soul in code, blocks dangers/PII, injects personality, generates verifiable ZK proofs for ethics compliance.
        """
    )

    with gr.Row():
        code_input = gr.Textbox(
            label="Your Code (Python, JS, PowerShell, etc. accepted)",
            lines=15,
            placeholder="# Paste your chaotic human code here...\n# TODO: add more pain",
            elem_id="code-box"
        )

    style_dropdown = gr.Dropdown(
        choices=["default", "2am_dev_rage", "corporate_clean", "chaotic_evil"],
        value="2am_dev_rage",
        label="Humanizer Style"
    )

    analyze_btn = gr.Button("Analyze →", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Results")
            breakdown_output = gr.JSON(label="Breakdown (why this score?)")
            humanized_output = gr.Textbox(label="Humanized Version", lines=10, interactive=False)
            proof_output = gr.Textbox(label="ZK Proof / Status", lines=3, interactive=False)
            status_output = gr.Textbox(label="Status", interactive=False)

    # Swarm votes placeholder
    swarm_output = gr.JSON(label="Swarm Votes")

    # Click handler
    analyze_btn.click(
        fn=analyze_code,
        inputs=[code_input, style_dropdown],
        outputs=[breakdown_output, humanized_output, proof_output, status_output]
    )

    # Quick examples
    gr.Examples(
        examples=[
            ["# Example - low soul\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)"],
            ["# GOD WHY\nprint('pain')\ndef chaos():\n    print('send help ☕')"],
        ],
        inputs=code_input
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        debug=True,  # shows errors in console/logs
        show_error=True
    )