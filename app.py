import gradio as gr
import re
import random
import statistics
import hashlib
import time
import zipfile
import os
import shutil
import tempfile
import math
from collections import Counter
from pathlib import Path
from difflib import unified_diff

# ────────────────────────────────────────────────
#   HELPER FUNCTIONS
# ────────────────────────────────────────────────

def detect_language(code: str) -> str:
    code_lower = code.lower()
    if re.search(r'\b(using\s+system|namespace|class|public|private|protected|static|void|async|await|var|interface|struct|enum|delegate|event)\b', code_lower):
        return "csharp"
    if re.search(r'\b(public|private|protected|class|interface|enum|extends|implements|import\s+java|package|static|void|final|synchronized)\b', code_lower):
        return "java"
    if re.search(r'\b(def|class|import|from\s+\w+\s+import)\b', code_lower):
        return "python"
    if re.search(r'\b(function|const|let|var|class|=>)\b', code_lower):
        return "javascript"
    if re.search(r'\b#include|<.*?>|std::|cout|cin\b', code_lower):
        return "cpp"
    return "generic"

def get_comment_styles(lang: str):
    if lang == "python":
        return {"single": "#", "multi_start": '"""', "multi_end": '"""'}
    if lang in ("javascript", "cpp", "java", "csharp"):
        return {"single": "//", "multi_start": "/*", "multi_end": "*/"}
    return {"single": "//", "multi_start": "/*", "multi_end": "*/"}

# ────────────────────────────────────────────────
#   ANALYZER (improved original soul scoring)
# ────────────────────────────────────────────────

def calculate_soul_score(code: str):
    if not code.strip():
        return "0%", "Empty", "NO CODE", "REJECTED", "No input", code, "Tier X - Invalid", "N/A", ""

    lines = code.splitlines()
    non_empty = [l.strip() for l in lines if l.strip()]

    # ── Bonuses ─────────────────────────────────────
    comments = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*', '"""', "'''")))
    markers = len(re.findall(r'\b(TODO|FIXME|HACK|NOTE|BUG|XXX|WTF|DEBUG)\b', code, re.I))
    comment_bonus = min(comments * 1.8 + markers * 12, 55)

    vars_found = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{2,}\b', code)
    meaningful_vars = [v for v in vars_found if v not in {'def','if','for','return','else','True','False','None','self','const','let','var'}]
    if meaningful_vars:
        lengths = [len(v) for v in meaningful_vars]
        avg = statistics.mean(lengths)
        std = statistics.stdev(lengths) if len(lengths) > 1 else 0
        naming_bonus = min(avg * 4 + std * 8, 35)
    else:
        naming_bonus = 0

    branches = sum(code.count(kw) for kw in ['if ', 'elif ', 'for ', 'while ', 'try:', 'except', 'switch', 'case'])
    nesting_proxy = sum(max(0, (len(l) - len(l.lstrip())) // 2) for l in lines if l.strip())
    complexity_bonus = min((branches * 3 + nesting_proxy * 2), 40)

    total_bonus = comment_bonus + naming_bonus + complexity_bonus

    # ── Penalties ───────────────────────────────────
    stripped_lines = [l.strip() for l in lines if l.strip()]
    dup_ratio = sum(c > 1 for c in Counter(stripped_lines).values()) / max(len(stripped_lines), 1)
    repetition_penalty = dup_ratio * -60

    line_lengths = [len(l) for l in non_empty]
    len_std = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0
    simplicity_penalty = -max(0, 30 - len_std * 1.5)

    risky = 0
    lower = code.lower()
    dangerous = ["eval(", "exec(", "os.system(", "subprocess.", "pickle.load", "rm -rf", "format c:", "del *.*"]
    secrets = ["password = ", "api_key = ", "secret = ", "token = ", "key = ", "hardcoded"]
    bare_except = len(re.findall(r'except\s*(?::|\))', code)) + len(re.findall(r'except\s+[A-Za-z]+\s*:', code)) > 3
    risky += sum(1 for pat in dangerous + secrets if pat in lower)
    risky += bare_except * 2
    risk_penalty = risky * -25

    total_penalty = repetition_penalty + simplicity_penalty + risk_penalty

    # ── Final ───────────────────────────────────────
    score = 45 + total_bonus + total_penalty
    score = max(5, min(98, round(score)))
    score_str = f"{score}% Human Soul"

    energy = "Vata Full Soul 🔥" if score >= 82 else "Strong Vata Pulse" if score >= 65 else "Hybrid Aura" if score >= 45 else "Soulless Void"
    cls = "HUMAN" if score > 78 else "MACHINE / HYBRID" if score > 50 else "AI-TRACED"
    verdict = "VATA APPROVED" if score >= 78 and risky <= 1 else "VATA FLAGGED" if score >= 45 else "VATA REJECTED"
    if risky >= 3:
        verdict = "VATA BLOCKED - SECURITY VIOLATIONS"

    tier = "S+ Trusted Artisan" if score >= 90 else "S Solid Human" if score >= 78 else "A Probable Safe" if score >= 62 else "B Needs Eyes" if score >= 45 else "C High Risk"

    timestamp = int(time.time())
    proof_input = f"{code.strip()}|{score_str}|{verdict}|{timestamp}"
    proof_hash = hashlib.sha256(proof_input.encode()).hexdigest()[:16].upper()
    proof = f"VATA-PROOF-{proof_hash}\nVerify: SHA256({proof_input})"

    violations = "\n".join([f"• {v}" for v in [
        "Dangerous execution calls" if any(p in lower for p in dangerous[:3]) else None,
        "Potential secrets/hardcoded creds" if any(p in lower for p in secrets) else None,
        "Destructive shell patterns" if any(p in lower for p in dangerous[5:]) else None,
        "Bare/broad excepts (risky)" if bare_except else None,
    ] if v]) or "Clean"

    return score_str, energy, cls, verdict, violations, code, tier, proof

# ────────────────────────────────────────────────
#   HUMANIZER – the part that adds teeth
# ────────────────────────────────────────────────

def humanize_code(code: str, intensity: int, add_debug: bool, sarcastic: bool, inconsistent: bool, personal_names: bool, redundancies: bool):
    if not code.strip():
        return code

    lang = detect_language(code)
    comments = get_comment_styles(lang)
    single = comments["single"]

    lines = code.splitlines()
    new_lines = []

    # Intensity scaling (0–10 → multiplier)
    factor = intensity / 10.0
    chance_comment      = 0.25 * factor
    chance_debug        = 0.20 * factor if add_debug else 0
    chance_sarcastic    = 0.18 * factor if sarcastic else 0
    chance_inconsistent = 0.35 * factor if inconsistent else 0
    chance_rename       = 0.22 * factor if personal_names else 0
    chance_redundant    = 0.15 * factor if redundancies else 0

    # ── Personal rename dictionary (applied sparingly) ──
    rename_map = {
        "input_data":   "rawInput",
        "result":       "finalRes",
        "data":         "stuff",
        "user":         "whoever",
        "config":       "settingsYo",
        "response":     "resp",
        "output":       "out",
        "value":        "val",
    }

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Occasionally skip indent consistency
        if inconsistent and random.random() < 0.08 * factor:
            indent = line[:len(line) - len(stripped)]
            if random.random() < 0.5:
                new_lines.append(indent.replace("    ", "  ") + stripped)  # mix 2/4 spaces
            else:
                new_lines.append(indent + " " + stripped)  # random extra space
        else:
            new_lines.append(line)

        # Add comment block sometimes
        if stripped and random.random() < chance_comment:
            if random.random() < 0.6:
                new_lines.append(f"{line[:len(line)-len(stripped)]}{single} {random.choice(['TODO: revisit', 'FIXME later', 'this is cursed but works', 'god why', 'borrowed from stackoverflow 2018'])}")
            else:
                new_lines.append(f"{line[:len(line)-len(stripped)]}{single} {random.choice(['cleaned up', 'optimized?', 'works on my machine', 'legacy reasons'])}")

        # Debug print / log
        if add_debug and stripped and random.random() < chance_debug and i < len(lines)-1:
            debug_strs = {
                "python": f"print(f'DEBUG: {{ {stripped.split()[0]} = }}')",
                "javascript": f"console.log('→', {stripped.split('=')[0].strip() if '=' in stripped else 'here'})",
                "java": f"System.out.println(\"DEBUG: \" + {stripped.split('=')[0].strip() if '=' in stripped else '\"here\"'});",
                "cpp": f"std::cout << \"DEBUG: \" << {stripped.split('=')[0].strip() if '=' in stripped else '\"here\"'} << std::endl;",
                "csharp": f"Console.WriteLine(\"DEBUG: \" + {stripped.split('=')[0].strip() if '=' in stripped else '\"here\"'});",
                "generic": f"{single} debug: {stripped[:30]}..."
            }
            new_lines.append(f"{line[:len(line)-len(stripped)]}{debug_strs.get(lang, debug_strs['generic'])}  {single} temp")

        # Sarcastic comment
        if sarcastic and random.random() < chance_sarcastic:
            sassy = random.choice([
                f"{single} why do we even...",
                f"{single} future me: I'm so sorry",
                f"{single} if you're reading this: send help",
                f"{single} enterprise quality™",
            ])
            new_lines.append(f"{line[:len(line)-len(stripped)]}{sassy}")

        # Redundancy (harmless)
        if redundancies and random.random() < chance_redundant and "return" in stripped:
            new_lines.append(f"{line[:len(line)-len(stripped)]}temp = {stripped.split('return ')[1]}")
            new_lines.append(f"{line[:len(line)-len(stripped)]}return temp  {single} explicit")

        # Personal rename (simple replace, only identifiers)
        if personal_names and random.random() < chance_rename:
            for old, new in rename_map.items():
                if random.random() < 0.4:
                    line = re.sub(r'\b' + re.escape(old) + r'\b', new, line)

        i += 1

    # Final touch: random trailing whitespace on ~10% lines
    for j in range(len(new_lines)):
        if random.random() < 0.12 * factor:
            new_lines[j] = new_lines[j].rstrip() + "  "

    humanized = "\n".join(new_lines)

    # Quick integrity note
    short_hash = hashlib.sha256(humanized.encode()).hexdigest()[:8].upper()
    humanized += f"\n\n# Humanized VATA-touch – hash {short_hash} – intensity {intensity}/10"

    return humanized

# ────────────────────────────────────────────────
#   Gradio INTERFACE
# ────────────────────────────────────────────────

custom_css = """
body { background: linear-gradient(135deg, #0a0015, #1a0033); color: #00ff9d; font-family: 'Courier New', monospace; }
.gradio-container { border: 2px solid #00ff9d; border-radius: 12px; background: rgba(5,5,25,0.85); max-width: 1100px; margin: auto; }
h1, h2 { color: #00ff9d; text-shadow: 0 0 12px #00ff9d; }
button { background: #00ff9d !important; color: black !important; border: none; border-radius: 6px; }
button:hover { box-shadow: 0 0 18px #00ff9d; }
"""

with gr.Blocks(css=custom_css, title="VATA Soul Check – Real Edition") as demo:
    gr.Markdown("# VATA Soul Check 2026 – Human vs Machine Reality Check")
    gr.Markdown("Analyzer scores code soul. Humanizer makes AI code look hand-written. Use both.")

    with gr.Tab("Analyzer (Detect)"):
        with gr.Row():
            code_in = gr.Textbox(lines=18, label="Paste Code", placeholder="Any language…")
        with gr.Row():
            analyze_btn = gr.Button("Run VATA Soul Scan", variant="primary")
        with gr.Row():
            score_out      = gr.Textbox(label="Soul Score")
            energy_out     = gr.Textbox(label="Energy")
            class_out      = gr.Textbox(label="Classification")
            verdict_out    = gr.Textbox(label="Verdict")
        with gr.Row():
            viol_out       = gr.Textbox(label="Violations / Risks", lines=3)
            tier_out       = gr.Textbox(label="Trust Tier")
            proof_out      = gr.Textbox(label="VATA Proof (SHA256)", lines=3)
        analyze_btn.click(
            calculate_soul_score,
            inputs=code_in,
            outputs=[score_out, energy_out, class_out, verdict_out, viol_out, code_in, tier_out, proof_out]
        )

    with gr.Tab("Humanizer (Make it Human)"):
        with gr.Row():
            code_in_h = gr.Textbox(lines=18, label="Paste (AI) Code to Humanize")
        with gr.Row():
            intensity = gr.Slider(1, 10, value=5, step=1, label="Humanization Intensity")
            add_debug = gr.Checkbox(label="Add debug prints/logs", value=True)
            sarcastic = gr.Checkbox(label="Sarcastic / personal comments", value=True)
            inconsistent = gr.Checkbox(label="Inconsistent formatting", value=True)
            personal_names = gr.Checkbox(label="Personal / quirky variable names", value=True)
            redundancies = gr.Checkbox(label="Harmless redundancies", value=False)
        with gr.Row():
            humanize_btn = gr.Button("Humanize Code", variant="primary")
        humanized_out = gr.Textbox(lines=22, label="Humanized Output")
        humanize_btn.click(
            humanize_code,
            inputs=[code_in_h, intensity, add_debug, sarcastic, inconsistent, personal_names, redundancies],
            outputs=humanized_out
        )

    gr.Markdown("Built by @Lhmisme | Now with actual configurable teeth – 2026")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)