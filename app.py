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
            "No proof generated",
        )

    lines = code.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]

    comments = sum(
        1 for l in lines
        if l.strip().startswith(("#", "//", "/*", "*", '"""', "'''"))
    )
    markers = len(re.findall(r"\b(TODO|FIXME|HACK|NOTE|BUG|XXX)\b", code, re.I))
    comment_bonus = (comments / max(len(non_empty_lines), 1) * 40) + (markers * 10)

    vars_found = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", code)
    meaningful_vars = [
        v for v in vars_found
        if len(v) > 2 and v not in {"def", "if", "for", "return", "else", "True", "False", "None", "self"}
    ]

    naming_bonus = 0
    if meaningful_vars:
        lengths = [len(v) for v in meaningful_vars]
        avg_len = sum(lengths) / len(lengths)
        std_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
        naming_bonus = (avg_len * 3) + (std_len * 5)

    branches = sum(code.count(kw) for kw in ["if ", "elif ", "for ", "while ", "try:", "except", "with "])
    nesting = sum(max(0, (len(l) - len(l.lstrip())) // 4) for l in lines if l.strip())
    complexity_bonus = min((branches + nesting) * 2, 30)

    total_bonus = comment_bonus + naming_bonus + complexity_bonus

    stripped_lines = [l.strip() for l in lines if l.strip()]
    dup_ratio = sum(c > 1 for c in Counter(stripped_lines).values()) / max(len(stripped_lines), 1)
    repetition_penalty = dup_ratio * -50

    line_lengths = [len(l) for l in non_empty_lines]
    len_std = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0
    simplicity_penalty = -max(0, 25 - len_std * 1.2)

    lower = code.lower()
    risky = 0
    risky += any(kw in lower for kw in ["eval(", "exec(", "os.system(", "subprocess.", "pickle.load", "rm -rf", "format c:", "del *.*"])
    risky += any(p in lower for p in ["password =", "api_key =", "secret =", "token =", "hardcoded"])
    risky += sum(1 for pat in [r"except\s*:", r"except Exception\s*:"] if re.search(pat, code))

    risk_penalty = risky * -20
    total_penalty = repetition_penalty + simplicity_penalty + risk_penalty

    score = 40 + total_bonus + total_penalty
    score = max(5, min(95, round(score)))
    score_str = f"{score}%"

    energy = "Full Soul" if score >= 80 else "Medium Soul" if score >= 60 else "Hybrid" if score >= 40 else "Soulless"
    cls = "HUMAN SOUL" if score > 70 else "MACHINE / HYBRID" if score > 40 else "SOULLESS"
    verdict = "VATA COMPLIANT" if score > 70 and risky == 0 else "VATA REVIEW NEEDED" if score > 40 else "VATA REJECTED"
    if risky > 0:
        verdict = "VATA REJECTED (Violations)"

    tier = "Tier S - Trusted Human" if score >= 80 else "Tier A - Likely Safe" if score >= 60 else "Tier B - Review Recommended" if score >= 40 else "Tier C - High Risk"
    confidence = "High" if risky > 0 or score > 80 else "Medium"

    timestamp = int(time.time())
    proof_input = f"{code}|{score_str}|{verdict}|{timestamp}"
    proof_hash = hashlib.sha256(proof_input.encode()).hexdigest()
    proof_text = f"Integrity Proof (SHA256): {proof_hash}\nVerify: {proof_input}\n(Compute SHA256 to confirm)"

    violations = []
    if any(kw in lower for kw in ["os.system(", "subprocess.", "exec(", "eval("]):
        violations.append("Dangerous ops")
    if any(p in lower for p in ["password =", "api_key =", "secret ="]):
        violations.append("Hardcoded secrets")
    if any(p in lower for p in ["rm -rf", "del *.*", "format "]):
        violations.append("Destructive cmds")
    violations_text = "\n".join(f"- {v}" for v in violations) if violations else "None detected"

    return (
        score_str,
        energy,
        cls,
        verdict,
        violations_text,
        code,
        tier,
        confidence,
        proof_text,
    )

demo = gr.Interface(
    fn=calculate_soul_score,
    inputs=gr.Textbox(lines=15, label="Paste Code Here"),
    outputs=[
        gr.Textbox(label="Score"),
        gr.Textbox(label="Energy Level"),
        gr.Textbox(label="Classification"),
        gr.Textbox(label="Verdict"),
        gr.Textbox(label="Violations"),
        gr.Textbox(label="Input Code"),
        gr.Textbox(label="Trust Tier"),
        gr.Textbox(label="Confidence"),
        gr.Textbox(label="Integrity Proof"),
    ],
    title="VATA Code Analyzer",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
