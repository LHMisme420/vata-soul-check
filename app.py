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
#   ANALYZER
# ────────────────────────────────────────────────

def calculate_soul_score(code: str):
    if not code.strip():
        return "0%", "Empty", "NO CODE", "REJECTED", "Tier X - Invalid"

    lang = detect_language(code)
    lines = code.splitlines()
    non_empty = [l.strip() for l in lines if l.strip()]

    comments = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*', '"""', "'''")))
    markers = len(re.findall(r'\b(TODO|FIXME|HACK|NOTE|BUG|XXX|WTF|DEBUG)\b', code, re.I))
    comment_bonus = min(comments * 1.8 + markers * 12, 55)

    vars_found = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{2,}\b', code)
    exclude = {'def','if','for','return','else','True','False','None','self','const','let','var',
               'public','private','protected','static','void','final','using','namespace','async','await'}
    meaningful_vars = [v for v in vars_found if v not in exclude]
    naming_bonus = 0
    if meaningful_vars:
        lengths = [len(v) for v in meaningful_vars]
        avg = statistics.mean(lengths) if lengths else 0
        std = statistics.stdev(lengths) if len(lengths) > 1 else 0
        naming_bonus = min(avg * 4 + std * 8, 35)

    branch_kws_base = ['if ', 'elif ', 'for ', 'while ', 'try:', 'except', 'switch', 'case']
    branch_kws_java = ['catch', 'final', 'synchronized'] if lang == "java" else []
    branch_kws_csharp = ['catch', 'finally', 'foreach', 'lock', 'checked', 'unchecked'] if lang == "csharp" else []
    branches = sum(code.count(kw) for kw in branch_kws_base + branch_kws_java + branch_kws_csharp)

    indent_nesting = sum(max(0, (len(l) - len(l.lstrip())) // 2) for l in lines if l.strip())
    brace_nesting = code.count('{') - code.count('}')
    nesting_proxy = indent_nesting + abs(brace_nesting) * 2 if lang in ("java", "javascript", "cpp", "csharp") else indent_nesting
    complexity_bonus = min((branches * 3 + nesting_proxy * 2), 40)

    total_bonus = comment_bonus + naming_bonus + complexity_bonus

    stripped_lines = [l.strip() for l in lines if l.strip()]
    dup_ratio = sum(c > 1 for c in Counter(stripped_lines).values()) / max(len(stripped_lines), 1) if stripped_lines else 0
    repetition_penalty = dup_ratio * -60

    line_lengths = [len(l) for l in non_empty]
    len_std = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0
    simplicity_penalty = -max(0, 30 - len_std * 1.5)

    risky = 0
    lower = code.lower()
    dangerous_base = ["eval(", "exec(", "os.system(", "subprocess.", "pickle.load", "rm -rf", "format c:", "del *.*"]
    dangerous_java = ["runtime.getruntime().exec(", "processbuilder(", "system.setsecuritymanager(null)", "thread.sleep(", "reflection"] if lang == "java" else []
    dangerous_csharp = ["process.start(", "system.diagnostics.process(", "file.delete(", "directory.delete(", "thread.sleep(", "reflection"] if lang == "csharp" else []
    secrets = ["password =", "api_key =", "secret =", "token =", "key =", "hardcoded"]
    bare_except_py = len(re.findall(r'except\s*(?::|\))', code)) + len(re.findall(r'except\s+[A-Za-z]+\s*:', code)) > 3
    bare_catch = len(re.findall(r'\}\s*catch\s*\(\s*Exception\s*\w*\)\s*\{', code)) > 1 if lang in ("java", "csharp") else 0
    risky += sum(lower.count(pat) for pat in dangerous_base + dangerous_java + dangerous_csharp + secrets)
    risky += (bare_except_py + bare_catch) * 2
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
#   HUMANIZER – highly configurable
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

    intensities = {
        'comment': comment_intensity / 10,
        'debug': debug_intensity / 10,
        'sarcasm': sarcasm_intensity / 10,
        'inconsistency': inconsistency_intensity / 10,
        'rename': rename_intensity / 10,
        'redundancy': redundancy_intensity / 10
    }

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

        if random.random() < intensities['inconsistency'] * 0.3:
            if random.random() < 0.5:
                new_lines[i] = line.replace("    ", "  ")
            else:
                new_lines[i] += "  "

        if stripped and random.random() < intensities['comment'] * 0.4:
            comment = random.choice(comments_list)
            new_lines.insert(i+1, f"{line[:len(line)-len(stripped)]}{single} {comment}")

        if random.random() < intensities['debug'] * 0.25:
            debug_line = f"{debug_prefix} here"
            if lang == "python":
                debug_line = f"print('{debug_prefix} entering line {i+1}')"
            elif lang in ("javascript", "java", "csharp"):
                debug_line = f"console.log('{debug_prefix} line {i+1}')"
            new_lines.insert(i+1, f"{line[:len(line)-len(stripped)]}{debug_line}")

        if random.random() < intensities['sarcasm'] * 0.2:
            sassy = random.choice(["why...", "future me is sorry", "send coffee", "this is cursed"])
            new_lines.insert(i+1, f"{line[:len(line)-len(stripped)]}{single} {sassy}")

        if random.random() < intensities['redundancy'] * 0.15 and "return" in stripped:
            expr = stripped.split("return ", 1)[1]
            new_lines.insert(i, f"{line[:len(line)-len(stripped)]}temp = {expr}")
            new_lines[i+1] = f"{line[:len(line)-len(stripped)]}return temp  {single} explicit"

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
#   Gradio INTERFACE – with auto-scoring in Humanizer
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

with gr.Blocks(css=custom_css, title="VATA Soul Check – Auto-Scoring Edition") as demo:
    gr.Markdown("# VATA Soul Check – Auto-Scoring Humanizer")
    gr.Markdown("Humanize code → instantly see before/after soul scores & delta")

    code_in = gr.Textbox(lines=16, label="Paste Code (AI or any)", placeholder="Paste code here...")

    with gr.Row():
        lang_override = gr.Dropdown(
            choices=["Auto", "Python", "Java", "C#", "JavaScript", "C++", "Other"],
            value="Auto", label="Force Language"
        )
        intensity_global = gr.Slider(0, 10, value=5, step=0.5, label="Global Intensity")

    with gr.Accordion("Detailed Controls (optional)", open=False):
        with gr.Row():
            comment_int = gr.Slider(0, 10, value=5, label="Comment Intensity")
            debug_int   = gr.Slider(0, 10, value=5, label="Debug Intensity")
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

    btn_humanize = gr.Button("Humanize + Auto-Score", variant="primary")

    humanized_out = gr.Textbox(lines=14, label="Humanized Output", interactive=False)

    with gr.Row():
        orig_score   = gr.Textbox(label="Original Score")
        new_score    = gr.Textbox(label="Humanized Score")
        delta_badge  = gr.HTML(label="Delta / Improvement")
        energy_out   = gr.Textbox(label="Energy (after)")
        cls_out      = gr.Textbox(label="Classification (after)")
        verdict_out  = gr.Textbox(label="Verdict (after)")

    # ── Auto-score after humanization ──
    def humanize_and_score(code, lang_ovr, glob_int, c_int, d_int, s_int, i_int, r_int, rd_int, c_preset, n_style, dbg_pre):
        if not code.strip():
            return "", "0%", "0%", "<span class='danger'>No code</span>", "", "", ""

        humanized = humanize_code(
            code, glob_int, c_int, d_int, s_int, i_int, rd_int,
            comment_style_preset=c_preset, naming_style=n_style,
            debug_prefix=dbg_pre, language_override=lang_ovr
        )

        o_score, o_energy, o_cls, o_verdict, o_tier = calculate_soul_score(code)
        h_score, h_energy, h_cls, h_verdict, h_tier = calculate_soul_score(humanized)

        o_num = int(o_score.rstrip("%")) if "%" in o_score else 0
        h_num = int(h_score.rstrip("%")) if "%" in h_score else 0
        delta = h_num - o_num

        badge_class = 'success' if delta > 20 else 'warning' if delta > 0 else 'danger'
        badge = f"<span class='output-badge {badge_class}'>{delta:+}%</span>"

        return (
            humanized,
            o_score,
            h_score,
            badge,
            h_energy,
            h_cls,
            h_verdict
        )

    btn_humanize.click(
        humanize_and_score,
        inputs=[
            code_in, lang_override, intensity_global,
            comment_int, debug_int, sarcasm_int,
            incon_int, rename_int, redund_int,
            comment_preset, naming_style, debug_prefix
        ],
        outputs=[
            humanized_out,
            orig_score,
            new_score,
            delta_badge,
            energy_out,
            cls_out,
            verdict_out
        ]
    )

    gr.Markdown("Auto-scoring enabled – see improvement instantly | Built by @Lhmisme | 2026")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)