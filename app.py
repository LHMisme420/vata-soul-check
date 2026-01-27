import gradio as gr
import hashlib
import random  # for dummy humanization

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

    # Mock ZK status (real snarkjs integration requires local circuit files committed to repo)
    zk_status = (
        "ZK-SNARK proof generated (vPoC - mock mode on HF Spaces)\n"
        "Ethics compliant (hash: deadbeef123)\n"
        "For real ZKP: Compile Circom locally, commit files, update to use subprocess with snarkjs"
    )

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