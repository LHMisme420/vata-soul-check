import gradio as gr
import re
import random
import statistics
import hashlib
import time
from collections import Counter

# ────────────────────────────────────────────────
#   LANGUAGE & COMMENT HELPERS
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
    return "other"

def get_comment_styles(lang: str):
    styles = {
        "python": {"single": "#", "multi_start": '"""', "multi_end": '"""'},
        "javascript": {"single": "//", "multi_start": "/*", "multi_end": "*/"},
        "java": {"single": "//", "multi_start": "/**", "multi_end": "*/"},
        "csharp": {"single": "//", "multi_start": "/*", "multi_end": "*/"},
        "cpp": {"single": "//", "multi_start": "/*", "multi_end": "*/"},
        "other": {"single": "//", "multi_start": "/*", "multi_end": "*/"}
    }
    return styles.get(lang, styles["other"])

# ────────────────────────────────────────────────
#   ANALYZER (unchanged core logic)
# ────────────────────────────────────────────────

def calculate_soul_score(code: str):
    if not code.strip():
        return "0%", "Empty", "NO CODE", "REJECTED", "No input", code, "Tier X - Invalid", "N/A", ""

    lines = code.splitlines()
    non_empty = [l.strip() for l in lines if l.strip()]

    comments = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*', '"""', "'''")))
    markers = len(re.findall(r'\b(TODO|FIXME|HACK|NOTE|BUG|XXX|WTF|DEBUG)\b', code, re.I))
    comment_bonus = min(comments * 1.8 + markers * 12, 55)

    vars_found = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{2,}\b', code)
    meaningful_vars = [v for v in vars_found if v not in {'def','if','for','return','else','True','False','None','self','const','let','var'}]
    naming_bonus = 0
    if meaningful_vars:
        lengths = [len(v) for v in meaningful_vars]
        avg = statistics.mean(lengths)
        std = statistics.stdev(lengths) if len(lengths) > 1 else 0
        naming_bonus = min(avg * 4 + std * 8, 35)

    branches = sum(code.count(kw) for kw in ['if ', 'elif ', 'for ', 'while ', 'try:', 'except', 'switch', 'case'])
    nesting_proxy = sum(max(0, (len(l) - len(l.lstrip())) // 2) for l in lines if l.strip())
    complexity_bonus = min((branches * 3 + nesting_proxy * 2), 40)

    total_bonus = comment_bonus + naming_bonus + complexity_bonus

    stripped_lines = [l.strip() for l in lines if l.strip()]
    dup_ratio = sum(c > 1 for c in Counter(stripped_lines).values()) / max(len(stripped_lines), 1)
    repetition_penalty = dup_ratio * -60

    line_lengths = [len(l) for l in non_empty]
    len_std = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0
    simplicity_penalty = -max(0, 30 - len_std * 1.5)

    risky = 0
    lower = code.lower()
    dangerous = ["eval(", "exec(", "os.system(", "subprocess.", "pickle.load", "rm -rf", "format c:", "del *.*"]
    secrets = ["password =", "api_key =", "secret =", "token =", "key =", "hardcoded"]
    bare_except = len(re.findall(r'except\s*(?::|\))', code)) + len(re.findall(r'except\s+[A-Za-z]+\s*:', code)) > 3
    risky += sum(1 for pat in dangerous + secrets if pat in lower)
    risky += bare_except * 2
    risk_penalty = risky * -25

    total_penalty = repetition_penalty + simplicity_penalty + risk_penalty

    score = 45 + total_bonus + total_penalty
    score = max(5, min(98, round(score)))
    score_str = f"{score}%"

    energy = "Vata Full Soul 🔥" if score >= 82 else "Strong Vata Pulse ⚡" if score >= 65 else "Hybrid Aura 🌫️" if score >= 45 else "Soulless Void 🕳️"
    cls = "HUMAN" if score > 78 else "MACHINE / HYBRID" if score > 50 else "AI-TRACED"
    verdict = "VATA APPROVED ✅" if score >= 78 and risky <= 1 else "VATA FLAGGED ⚠️" if score >= 45 else "VATA REJECTED ❌"
    if risky >= 3:
        verdict = "VATA BLOCKED - SECURITY VIOLATIONS ⛔"

    tier = "S+ Trusted Artisan" if score >= 90 else "S Solid Human" if score >= 78 else "A Probable Safe" if score >= 62 else "B Needs Eyes" if score >= 45 else "C High Risk"

    return score_str, energy, cls, verdict, tier

# ────────────────────────────────────────────────
#   ADVANCED HUMANIZER – highly configurable
# ────────────────────────────────────────────────

def humanize_code(
    code: str,
    intensity: float = 5.0,
    comment_intensity: float = 5.0,
    debug_intensity: float = 5.0,
    sarcasm_intensity: float = 5.0,
    inconsistency_intensity: float = 5.0,
    rename_intensity: float = 5.0,
    redundancy_intensity: float = 3.0,
    comment_style_preset: str = "Casual",
    naming_style: str = "Random Flair",
    debug_prefix: str = "DEBUG:",
    language_override: str = "Auto"
):
    if not code.strip():
        return code

    lang = language_override if language_override != "Auto" else detect_language(code)
    comments = get_comment_styles(lang)
    single = comments["single"]

    lines = code.splitlines()
    new_lines = lines[:]

    # Normalize intensities to 0–1
    intensities = {
        'comment': comment_intensity / 10,
        'debug': debug_intensity / 10,
        'sarcasm': sarcasm_intensity / 10,
        'inconsistency': inconsistency_intensity / 10,
        'rename': rename_intensity / 10,
        'redundancy': redundancy_intensity / 10
    }

    # Comment pool based on preset
    comment_pools = {
        "Casual": ['TODO: revisit later', 'maybe fix this someday', 'works for now', 'borrowed idea', 'not proud of this'],
        "Professional": ['Refactor opportunity', 'Consider extracting method', 'Documentation pending', 'Temporary solution', 'Needs review'],
        "Sarcastic": ['why do we even...', 'future me hates me', 'send help', 'enterprise quality™', 'this is fine.jpg'],
        "Minimal": ['todo', 'fixme', 'note', 'debug']
    }
    comments_list = comment_pools.get(comment_style_preset, comment_pools["Casual"])

    rename_map = {
        "input": "rawInput", "data": "stuff", "result": "finalRes", "value": "val",
        "user": "whoever", "config": "settingsYo", "response": "resp", "output": "out"
    }

    for i in range(len(new_lines)):
        line = new_lines[i]
        stripped = line.strip()

        # Inconsistency
        if random.random() < intensities['inconsistency'] * 0.3:
            if random.random() < 0.5:
                new_lines[i] = line.replace("    ", "  ")
            else:
                new_lines[i] += "  "

        # Comments
        if stripped and random.random() < intensities['comment'] * 0.4:
            comment = random.choice(comments_list)
            new_lines.insert(i+1, f"{line[:len(line)-len(stripped)]}{single} {comment}")

        # Debug
        if random.random() < intensities['debug'] * 0.25:
            debug_line = f"{debug_prefix} here"
            if lang == "python":
                debug_line = f"print('{debug_prefix} entering line {i+1}')"
            elif lang in ("javascript", "java", "csharp"):
                debug_line = f"console.log('{debug_prefix} line {i+1}')"
            new_lines.insert(i+1, f"{line[:len(line)-len(stripped)]}{debug_line}")

        # Sarcasm (extra layer on top of comments)
        if random.random() < intensities['sarcasm'] * 0.2:
            sassy = random.choice(["why...", "future me is sorry", "send coffee", "this is cursed"])
            new_lines.insert(i+1, f"{line[:len(line)-len(stripped)]}{single} {sassy}")

        # Redundancy
        if random.random() < intensities['redundancy'] * 0.15 and "return" in stripped:
            expr = stripped.split("return ", 1)[1]
            new_lines.insert(i, f"{line[:len(line)-len(stripped)]}temp = {expr}")
            new_lines[i+1] = f"{line[:len(line)-len(stripped)]}return temp  {single} explicit"

        # Rename
        if random.random() < intensities['rename'] * 0.3:
            for old, new in rename_map.items():
                if random.random() < 0.5:
                    line = re.sub(r'\b' + re.escape(old) + r'\b', new, line)
            new_lines[i] = line

    humanized = "\n".join(new_lines)

    short_hash = hashlib.sha256(humanized.encode()).hexdigest()[:8].upper()
    humanized += f"\n\n# VATA Humanized – hash {short_hash} – intensity {intensity:.1f}/10"

    return humanized

# ────────────────────────────────────────────────
#   Gradio INTERFACE – now super configurable
# ────────────────────────────────────────────────

custom_css = """
body { background: linear-gradient(135deg, #0a0015, #1a0033); color: #00ff9d; font-family: 'Courier New', monospace; }
.gradio-container { border: 2px solid #00ff9d; border-radius: 12px; background: rgba(5,5,25,0.85); max-width: 1300px; margin: auto; padding: 1rem; }
h1, h2 { color: #00ff9d; text-shadow: 0 0 12px #00ff9d; }
button { background: #00ff9d !important; color: black !important; border: none; border-radius: 6px; font-weight: bold; }
button:hover { box-shadow: 0 0 18px #00ff9d; }
.output-badge { font-weight: bold; padding: 6px 12px; border-radius: 6px; }
.success { background: #00cc66; color: black; }
.warning { background: #ffaa00; color: black; }
.danger { background: #ff4444; color: white; }
"""

with gr.Blocks(css=custom_css, title="VATA Soul Check – Fully Configurable") as demo:
    gr.Markdown("# VATA Soul Check – Fully Configurable Edition")
    gr.Markdown("Control every aspect of humanization. Analyzer + Humanizer in one place.")

    with gr.Tab("Humanizer + Analyzer"):
        code_in = gr.Textbox(lines=16, label="Paste Code (AI or any)", placeholder="Paste code here...")

        with gr.Row():
            lang_override = gr.Dropdown(
                choices=["Auto", "Python", "Java", "C#", "JavaScript", "C++", "Other"],
                value="Auto", label="Force Language"
            )
            intensity_global = gr.Slider(0, 10, value=5, step=0.5, label="Global Intensity")

        with gr.Accordion("Detailed Controls", open=False):
            with gr.Row():
                comment_int = gr.Slider(0, 10, value=5, label="Comment Intensity")
                debug_int   = gr.Slider(0, 10, value=5, label="Debug Print Intensity")
                sarcasm_int = gr.Slider(0, 10, value=5, label="Sarcasm Intensity")
            with gr.Row():
                incon_int   = gr.Slider(0, 10, value=5, label="Inconsistency Intensity")
                rename_int  = gr.Slider(0, 10, value=5, label="Rename Intensity")
                redund_int  = gr.Slider(0, 10, value=3, label="Redundancy Intensity")

            comment_preset = gr.Dropdown(
                choices=["Casual", "Professional", "Sarcastic", "Minimal"],
                value="Casual", label="Comment Style Preset"
            )
            naming_style = gr.Dropdown(
                choices=["Keep Original", "Random Flair", "Abbreviate", "CamelCase → snake_case"],
                value="Random Flair", label="Naming Style"
            )
            debug_prefix = gr.Textbox(value="DEBUG:", label="Debug Prefix")

        with gr.Row():
            btn_humanize = gr.Button("Humanize Code", variant="primary")
            btn_analyze  = gr.Button("Only Analyze (no change)", variant="secondary")

        humanized_out = gr.Textbox(lines=14, label="Humanized Output", interactive=False)
        with gr.Row():
            orig_score   = gr.Textbox(label="Original Score")
            new_score    = gr.Textbox(label="Humanized Score")
            delta_badge  = gr.HTML(label="Delta")

        # ── Run humanize + auto-score ──
        def humanize_and_score(code, lang_ovr, glob_int, c_int, d_int, s_int, i_int, r_int, rd_int, c_preset, n_style, dbg_pre):
            humanized = humanize_code(
                code, glob_int, d_int, s_int, i_int, r_int, rd_int,
                comment_style_preset=c_preset, naming_style=n_style,
                debug_prefix=dbg_pre, language_override=lang_ovr
            )
            o_score, _, _, _, _ = calculate_soul_score(code)
            h_score, _, _, _, _ = calculate_soul_score(humanized)
            delta = int(h_score.rstrip("%")) - int(o_score.rstrip("%"))
            badge = f"<span class='output-badge {'success' if delta > 20 else 'warning' if delta > 0 else 'danger'}'>{delta:+}%</span>"
            return humanized, o_score, h_score, badge

        btn_humanize.click(
            humanize_and_score,
            inputs=[code_in, lang_override, intensity_global, comment_int, debug_int, sarcasm_int, incon_int, rename_int, redund_int, comment_preset, naming_style, debug_prefix],
            outputs=[humanized_out, orig_score, new_score, delta_badge]
        )

        # ── Just analyze ──
        def only_analyze(code):
            score, energy, cls, verdict, tier = calculate_soul_score(code)
            return score, energy, cls, verdict, tier

        btn_analyze.click(
            only_analyze,
            inputs=code_in,
            outputs=[orig_score, gr.Textbox(label="Energy"), gr.Textbox(label="Classification"), gr.Textbox(label="Verdict"), gr.Textbox(label="Tier")]
        )

    gr.Markdown("Fully configurable – every slider matters | Built by @Lhmisme | 2026")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)