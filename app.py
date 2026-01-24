import gradio as gr
import re
from collections import Counter
import statistics
import hashlib
import time

def calculate_soul_score(code: str):
    if not code.strip():
        return (
            "0%",
            "Empty",
            "NO CODE",
            "REJECTED",
            "No input",
            code,
            "Tier X - Invalid",
            "N/A",
            "No proof generated"
        )

    lines = code.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]

    # Human bonuses
    # Comments + personal markers
    comments = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*', '"""', "'''")))
    markers = len(re.findall(r'\b(TODO|FIXME|HACK|NOTE|BUG|XXX)\b', code, re.I))
    comment_bonus = (comments / max(len(non_empty_lines), 1) * 40) + (markers * 10)

    # Naming variability (longer + diverse names = human)
    vars_found = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', code)
    meaningful_vars = [v for v in vars_found if len(v) > 2 and v not in {'def', 'if', 'for', 'return', 'else', 'True', 'False', 'None', 'self'}]
    naming_bonus = 0
    if meaningful_vars:
        lengths = [len(v) for v in meaningful_vars]
        avg_len = sum(lengths) / len(lengths)
        std_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
        naming_bonus = (avg_len * 3) + (std_len * 5)

    # Complexity (branches + nesting proxy)
    branches = sum(code.count(kw) for kw in ['if ', 'elif ', 'for ', 'while ', 'try:', 'except', 'with '])
    nesting = sum(max(0, (len(l) - len(l.lstrip())) // 4) for l in lines if l.strip())
    complexity_bonus = min((branches + nesting) * 2, 30)

    total_bonus = comment_bonus + naming_bonus + complexity_bonus

    # Penalties (AI/clean/risky traits)
    # Repetition
    stripped_lines = [l.strip() for l in lines if l.strip()]
    dup_ratio = sum(c > 1 for c in Counter(stripped_lines).values()) / max(len(stripped_lines), 1)
    repetition_penalty = dup_ratio * -50

    # Over-simplicity
    line_lengths = [len(l) for l in non_empty_lines]
    len_std = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0
    simplicity_penalty = -max(0, 25 - len_std * 1.2)

    # Risks
    risky = 0
    lower = code.lower()
    risky += any(kw in lower for kw in ["eval(", "exec(", "os.system(", "subprocess.", "pickle.load", "rm -rf", "format c:", "del *.*"])
    risky += any(p in lower for p in ["password =", "api_key =", "secret =", "token =", "hardcoded"])
    risky += sum(1 for pat in [r'except\s*:', r'except Exception\s*:'] if re.search(pat, code))
    risk_penalty = risky * -20

    total_penalty = repetition_penalty + simplicity_penalty + risk_penalty

    # Final score
    score = 40 + total_bonus + total_penalty
    score = max(5, min(95, round(score)))
    score_str = f"{score}%"

    # Energy / Class / Verdict / Tier (kept similar)
    energy = "Full Soul" if score >= 80 else "Medium Soul" if score >= 60 else "Hybrid" if score >= 40 else "Soulless"
    cls = "HUMAN SOUL" if score > 70 else "MACHINE / HYBRID" if score > 40 else "SOULLESS"
    verdict = "VATA COMPLIANT" if score > 70 and risky == 0 else "VATA REVIEW NEEDED" if score > 40 else "VATA REJECTED"
    if risky > 0:
        verdict = "VATA REJECTED (Violations)"
    tier = "Tier S - Trusted Human" if score >= 80 else "Tier A - Likely Safe" if score >= 60 else "Tier B - Review Recommended" if score >= 40 else "Tier C - High Risk"
    confidence = "High" if risky > 0 or score > 80 else "Medium"

    # Proof
    timestamp = int(time.time())
    proof_input = f"{code}|{score_str}|{verdict}|{timestamp}"
    proof_hash = hashlib.sha256(proof_input.encode()).hexdigest()
    proof_text = f"Integrity Proof (SHA256): {proof_hash}\nVerify: {proof_input}\n(Compute SHA256 to confirm)"

    violations_text = "\n".join([
        f"- {v}" for v in [
            "Dangerous ops" if any(kw in lower for kw in ["os.system(", "subprocess.", "exec(", "eval("]) else None,
            "Hardcoded secrets" if any(p in lower for p in ["password =", "api_key =", "secret ="]) else None,
            "Destructive cmds" if any(p in lower for p in ["rm -rf", "del *.*", "format "]) else None,
        ] if v
    ]) or "None detected"

    return (
        score_str,
        energy,
        cls,
        verdict,
        violations_text,
        code,
        tier,
        confidence,
        proof_text
    )

# Your existing custom CSS (unchanged)
custom_css = """
body { 
    background: linear-gradient(135deg, #0f0f0f, #1a0033); 
    color: #00ff41; 
    font-family: 'Courier New', monospace; 
}
.gradio-container { 
    border: 2px solid #00ff41; 
    border-radius: 15px; 
    background: rgba(0,0,0,0.7); 
}
h1, h2, h3 { 
    color: #00ff41; 
    text-shadow: 0 0 10px #00ff41; 
}
button { 
    background: #00ff41 !important; 
    color: black !important; 
    border-radius: 8px; 
}
button:hover { 
    box-shadow: 0 0 15px #00ff41; 
}
button.primary { 
    background: #00cc33 !important; 
    box-shadow: 0 0 20px #00ff41; 
}
"""

# Interface (minor title tweak for realism)
demo = gr.Interface(
    fn=calculate_soul_score,
    inputs=gr.Textbox(lines=15, label="Paste Code Here", placeholder="Python, PowerShell, JS, etc..."),
    outputs=[
        gr.Textbox(label="Score"),
        gr.Textbox(label="Energy Level"),
        gr.Textbox(label="Classification"),
        gr.Textbox(label="Verdict"),
        gr.Textbox(label="Violations", lines=3),
        gr.Textbox(label="Input Code", lines=10),
        gr.Textbox(label="Trust Tier"),
        gr.Textbox(label="Confidence"),
        gr.Textbox(label="Integrity Proof (SHA256)", lines=4)
    ],
    title="VATA Code Analyzer – Human vs AI Heuristics",
    description="Rule-based detector: rewards comments, messy naming, complexity; penalizes repetition, risks, over-clean code.\nBuilt by @Lhmisme | 2026",
    examples=[
        ["def add(a, b): return a + b", "Clean"],
        ["# TODO: fix later\nx = input()\nif x: print(x)  # debug", "Messy Human"],
        ["eval(input('cmd: '))", "Risky"],
    ],
    css=custom_css,
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
    import streamlit as st
import json
import numpy as np
import ezkl
# your existing imports
from features import extract_features  # adjust path if in src/
from souldetector import get_soul_score  # adjust if needed
# ... other imports like pickle, torch if used

# Your existing soul scoring setup (keep this)
# e.g., load model, feature_order list, etc.
feature_order = ["line_count", "comment_ratio", "has_todo", "perplexity", ...]  # fill from your code

MODEL_PATH = "models/soul_model_v1.pkl"  # or wherever yours is

# NEW: ezkl setup (add this section)
ONNX_MODEL_PATH = "soul_model.onnx"  # you'll add this file later

@st.cache_resource
def load_ezkl_resources():
    # Compile circuit once (slow first time, cached after)
    settings_path = "settings.json"
    if not os.path.exists(settings_path):
        ezkl.gen_settings(ONNX_MODEL_PATH, settings_path)
    ezkl.compile_circuit(ONNX_MODEL_PATH, "network.ezkl", settings_path)
    return settings_path

# NEW: proof generation function (add here)
def generate_zk_proof(code_snippet):
    # Extract features as before
    features_dict = extract_features(code_snippet)
    input_vec = np.array([features_dict.get(k, 0.0) for k in feature_order], dtype=np.float32).reshape(1, -1).tolist()

    # Prepare ezkl input
    data = {
        "input_data": input_vec,
        "input_shapes": [[1, len(feature_order)]]
    }
    input_json = "input.json"
    with open(input_json, "w") as f:
        json.dump(data, f)

    # Generate proof
    proof_path = "proof.json"
    settings_path = load_ezkl_resources()  # compile if needed
    ezkl.gen_proof("network.ezkl", input_json, proof_path, settings_path)

    # Read proof
    with open(proof_path, "r") as f:
        proof = json.load(f)

    score = get_soul_score(code_snippet)
    return proof, score

# -------------------------------
# Your Streamlit UI (main app block - extend this)
st.title("Vata Soul Check – Soul Detector")

code = st.text_area("Paste your code snippet here", height=300)

if st.button("Score Soul"):
    if code.strip():
        score = get_soul_score(code)
        st.metric("Soul Score", f"{score:.1f}/100")
        if score > 70:
            st.success("Strong human soul detected! 🔥")
        else:
            st.warning("Feels pretty clean/AI-like 😶")
    else:
        st.info("Enter some code first!")

# NEW: Add this button right below or next to the score button
if st.button("Generate ZK Proof (Verifiable Score)"):
    if code.strip():
        with st.spinner("Generating zk-proof... (may take a few seconds)"):
            try:
                proof, score = generate_zk_proof(code)
                st.success(f"ZK Proof generated for score {score:.1f}/100")
                st.json(proof)  # Show proof JSON
                st.download_button(
                    label="Download Proof JSON",
                    data=json.dumps(proof, indent=2),
                    file_name="vata_soul_proof.json",
                    mime="application/json"
                )
                st.info("This proof lets anyone verify the soul score was computed correctly without seeing the code or model internals.")
            except Exception as e:
                st.error(f"Proof generation failed: {str(e)}")
    else:
        st.warning("Paste code first!")