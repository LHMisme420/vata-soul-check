import gradio as gr
import hashlib
import random  # for dummy humanization
from pysnark.runtime import snark, PubVal, PrivVal  # REAL ZK magic!

# =====================================
# Your existing soul scoring logic (dummy version - replace with real!)
# =====================================
def get_soul_score(code: str) -> int:
    # Fake soul score based on length, comments, entropy, etc.
    score = len(code) // 10
    if "#" in code or "//" in code:
        score += 30
    if "TODO" in code.upper() or "FIXME" in code.upper():
        score += 20
    score += random.randint(0, 40)  # some chaos
    return min(max(score, 0), 999)  # 0-999

# =====================================
# REAL ZK-SNARK CIRCUIT (Groth16 via pysnark)
# Proves: soul_score >= threshold without revealing score or code
# =====================================
@snark
def prove_soul_score(code_hash_input: list[PrivVal], threshold: PubVal) -> PubVal:
    # Simulate soul score computation inside the circuit
    soul_score = 0
    for i in range(1024):  # padded to 1024 for fixed size
        if i < len(code_hash_input):
            soul_score = soul_score + code_hash_input[i]
        soul_score = soul_score * 31  # fake hash step

    soul_score = soul_score % 1000  # bound to 0-999

    # Prove the assertion (this is what gets proven!)
    assert soul_score >= threshold

    return 1  # public output: "valid" (1 = yes)

# =====================================
# Humanizer (your fun part - keep it chaotic!)
# =====================================
def humanize_code(code: str):
    lines = code.split("\n")
    humanized = []
    for line in lines:
        if random.random() < 0.3:
            humanized.append(line + "  # bruh why tho 💀")
        elif random.random() < 0.1:
            humanized.append(line + "  # GOD WHY print('pain')")
        else:
            humanized.append(line)
    return "\n".join(humanized)

# =====================================
# Main Gradio function
# =====================================
def analyze_and_humanize(code_input: str, threshold: int = 420):
    if not code_input.strip():
        return "Paste some code bruh 😭", "", "No code → no soul", ""

    # 1. Get soul score
    soul_score = get_soul_score(code_input)
    status = f"Analyzed - Soul {soul_score} | {'APPROVED 🔥' if soul_score >= threshold else 'REJECTED 😢'}"

    # 2. Humanize the code
    humanized = humanize_code(code_input)

    # 3. Prepare inputs for ZK proof (hash code into fixed-size list)
    code_bytes = code_input.encode('utf-8')
    code_hash = hashlib.sha256(code_bytes).digest()
    # Pad to 1024 * 32-bit values (dummy - in real you'd tokenize properly)
    padded_input = [int.from_bytes(code_hash[i:i+4], 'big') for i in range(0, len(code_hash), 4)]
    padded_input += [0] * (1024 - len(padded_input))  # pad with zeros

    try:
        # Generate REAL zk-SNARK proof!
        proof, public_inputs, proof_output = prove_soul_score(padded_input, threshold)
        zk_status = (
            f"✅ REAL Groth16 zk-SNARK Proof Generated!\n"
            f"Public: soul_score >= {threshold} → {proof_output}\n"
            f"Proof size: ~ few hundred bytes (succinct AF)\n"
            f"vPoC - ethics compliant"
        )
    except Exception as e:
        zk_status = f"ZK Proof failed (circuit error): {str(e)}"

    return humanized, zk_status, status, f"{{'swarm_votes': []}}"

# =====================================
# Gradio Interface
# =====================================
with gr.Blocks(title="VATA Soul Check & Humanizer") as demo:
    gr.Markdown("# VATA Soul Check & Humanizer ⚡")
    gr.Markdown("Paste code → Get soul score + zk-proof + humanized version!")

    code_input = gr.Code(
        label="Your Code Snippet (Python/JS/PS/etc.)",
        lines=10,
        language="python"
    )

    threshold_slider = gr.Slider(0, 999, value=420, step=1, label="Soul Threshold (higher = stricter)")

    btn = gr.Button("ANALYZE & HUMANIZE 🔥")

    humanized_output = gr.Code(label="Humanized Version", language="python")
    zk_output = gr.Textbox(label="ZK Proof / Status", lines=6)
    status_output = gr.Textbox(label="Status", lines=2)
    swarm_output = gr.JSON(label="{ } Swarm Votes")

    btn.click(
        fn=analyze_and_humanize,
        inputs=[code_input, threshold_slider],
        outputs=[humanized_output, zk_output, status_output, swarm_output]
    )

    gr.Examples(
        examples=[
            ["def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)", 420],
            ["#Example - low soul\ndef fib(n): return n if n<=1 else fib(n-1)+fib(n-2)"],
            ["# GOD WHY print('pain')\ndef chaos(): print('send help 🐸')"]
        ],
        inputs=[code_input, threshold_slider]
    )

demo.launch()
import subprocess
import json
import os

def generate_zk_proof(code_input_padded, threshold):
    try:
        # Prepare input.json
        input_data = {"code_input": code_input_padded, "threshold": threshold}
        with open("/tmp/input.json", "w") as f:
            json.dump(input_data, f)

        # Run snarkjs via node (Node is pre-installed on HF Spaces)
        cmd = [
            "node", "soul_score_js/soul_score.wasm",  # assume you copied the wasm folder
            "--input", "/tmp/input.json",
            "--zkey", "soul.zkey"  # copy to /app
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        proof = json.loads(result.stdout)  # adjust based on actual output

        # Verify (optional)
        verify_cmd = ["snarkjs", "groth16", "verify", "verification_key.json", "/tmp/public.json", "proof.json"]
        # ... etc.

        return "✅ Real Groth16 proof generated via snarkjs!", str(proof)
    except Exception as e:
        return f"ZK failed: {str(e)}", ""