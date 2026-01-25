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

# ────────────────────────────────────────────────
#   HELPERS
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

SUPPORTED_EXTS = {".py", ".java", ".cs", ".js", ".cpp", ".hpp", ".ts"}

# ────────────────────────────────────────────────
#   ANALYZER (same as Phase 1)
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
        avg = statistics.mean(lengths)
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
    dup_ratio = sum(c > 1 for c in Counter(stripped_lines).values()) / max(len(stripped_lines), 1)
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

    return score_str, energy, cls, verdict, tier, risky

# ────────────────────────────────────────────────
#   STYLE FINGERPRINT (simple stats from reference)
# ────────────────────────────────────────────────

def compute_style_fingerprint(code: str):
    if not code.strip():
        return {"comment_density": 0.15, "line_std": 15, "tab_ratio": 0.5, "var_entropy": 3.0}

    lines = [l for l in code.splitlines() if l.strip()]
    if not lines:
        return {"comment_density": 0.15, "line_std": 15, "tab_ratio": 0.5, "var_entropy": 3.0}

    comment_lines = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*', '"""', "'''")))
    comment_density = comment_lines / len(lines)

    line_lengths = [len(l) for l in lines]
    line_std = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 15

    tab_count = sum(l.count('\t') for l in lines)
    space_count = sum(l.count(' ') for l in lines if l.lstrip().startswith(' '))
    tab_ratio = tab_count / (tab_count + space_count + 1e-6) if space_count + tab_count > 0 else 0.5

    vars_found = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{2,}\b', code)
    if vars_found:
        lengths = [len(v) for v in vars_found]
        entropy = -sum((c / len(lengths)) * math.log2(c / len(lengths) + 1e-10) for c in Counter(lengths).values())
    else:
        entropy = 3.0

    return {
        "comment_density": comment_density,
        "line_std": line_std,
        "tab_ratio": tab_ratio,
        "var_entropy": entropy
    }

# ────────────────────────────────────────────────
#   HUMANIZER (enhanced with reference bias)
# ────────────────────────────────────────────────

def humanize_code(code: str, intensity: int, add_debug: bool, sarcastic: bool, inconsistent: bool, personal_names: bool, redundancies: bool, ref_fingerprint=None):
    if not code.strip():
        return code, "0%", "No code"

    lang = detect_language(code)
    comments = get_comment_styles(lang)
    single = comments["single"]

    lines = code.splitlines()
    new_lines = []

    factor = intensity / 10.0

    # Base chances, biased by reference if provided
    base_chance_comment = 0.25
    if ref_fingerprint:
        target_density = ref_fingerprint["comment_density"]
        current_density = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*', '"""', "'''"))) / max(1, len(lines))
        comment_bias = (target_density - current_density) * 2
        chance_comment = max(0.05, min(0.45, base_chance_comment + comment_bias))
    else:
        chance_comment = base_chance_comment * factor

    chance_debug        = 0.20 * factor if add_debug else 0
    chance_sarcastic    = 0.18 * factor if sarcastic else 0
    chance_inconsistent = 0.35 * factor if inconsistent else 0
    chance_rename       = 0.22 * factor if personal_names else 0
    chance_redundant    = 0.15 * factor if redundancies else 0

    rename_map = {
        "input_data": "rawInput", "result": "finalRes", "data": "stuff", "user": "whoever",
        "config": "settingsYo", "response": "resp", "output": "out", "value": "val",
    }

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Inconsistent indent biased toward ref tab_ratio
        if inconsistent and random.random() < chance_inconsistent:
            indent = line[:len(line) - len(stripped)]
            if ref_fingerprint and random.random() < ref_fingerprint["tab_ratio"]:
                indent = indent.replace("    ", "\t")  # bias to tabs
            if random.random() < 0.5:
                new_indent = indent.replace("    ", "  ")
            else:
                new_indent = indent + random.choice([" ", " "])
            new_lines.append(new_indent + stripped)
        else:
            new_lines.append(line)

        if stripped and random.random() < chance_comment:
            comment_text = random.choice(['TODO: revisit', 'FIXME later', 'this is cursed but works', 'god why', 'borrowed from stackoverflow 2018']) if random.random() < 0.6 else \
                           random.choice(['cleaned up', 'optimized?', 'works on my machine', 'legacy reasons'])
            new_lines.append(f"{line[:len(line)-len(stripped)]}{single} {comment_text}")

        if add_debug and stripped and random.random() < chance_debug and i < len(lines)-1:
            debug_strs = {
                "python": f"print(f'DEBUG: {{ {stripped.split()[0]} = }}')",
                "javascript": f"console.log('→', {stripped.split('=')[0].strip() if '=' in stripped else 'here'})",
                "java": f"System.out.println(\"DEBUG: \" + {stripped.split('=')[0].strip() if '=' in stripped else '\"here\"'});",
                "cpp": f"std::cout << \"DEBUG: \" << {stripped.split('=')[0].strip() if '=' in stripped else '\"here\"'} << std::endl;",
                "csharp": f"Console.WriteLine(\"DEBUG: \" + {stripped.split('=')[0].strip() if '=' in stripped else '\"here\"'});",
                "generic": f"{single} debug: {stripped[:30]}..."
            }
            debug_line = debug_strs.get(lang, debug_strs["generic"])
            new_lines.append(f"{line[:len(line)-len(stripped)]}{debug_line}  {single} temp")

        if sarcastic and random.random() < chance_sarcastic:
            sassy = random.choice([
                f"{single} why do we even...",
                f"{single} future me: I'm so sorry",
                f"{single} if you're reading this: send help",
                f"{single} enterprise quality™",
            ])
            new_lines.append(f"{line[:len(line)-len(stripped)]}{sassy}")

        if redundancies and random.random() < chance_redundant:
            if "return " in stripped:
                expr = stripped.split("return ", 1)[1]
                new_lines.append(f"{line[:len(line)-len(stripped)]}var temp = {expr};")
                new_lines.append(f"{line[:len(line)-len(stripped)]}return temp;  {single} explicit")
            elif lang in ("java", "csharp") and random.random() < 0.4:
                modifier = "final" if lang == "java" else "readonly"
                new_lines.insert(i, f"{line[:len(line)-len(stripped)]}{modifier} {stripped}  {single} why not")

        if personal_names and random.random() < chance_rename:
            for old, new in rename_map.items():
                if random.random() < 0.4:
                    line = re.sub(r'\b' + re.escape(old) + r'\b', new, line)
            new_lines[-1] = line

        i += 1

    # Trailing whitespace + line length variation bias
    for j in range(len(new_lines)):
        if random.random() < 0.12 * factor:
            new_lines[j] = new_lines[j].rstrip() + "  "
        # Slight length variation
        if ref_fingerprint and random.random() < 0.1:
            if random.random() < 0.5:
                new_lines[j] = new_lines[j] + "  # align"

    humanized = "\n".join(new_lines)
    short_hash = hashlib.sha256(humanized.encode()).hexdigest()[:8].upper()
    humanized += f"\n\n// Humanized VATA-touch – hash {short_hash} – intensity {intensity}/10"

    human_score, _, _, _, _, risky = calculate_soul_score(humanized)

    # Heuristic evasion confidence (0-95%)
    try:
        o_num = int(calculate_soul_score(code)[0].rstrip("%"))
        h_num = int(human_score.rstrip("%"))
        delta = h_num - o_num
        evasion = min(95, max(30, 40 + delta * 1.8 - risky * 10))
        if ref_fingerprint:
            evasion += 15  # bonus for style match
        evasion = min(95, evasion)
    except:
        evasion = 50

    return humanized, human_score, short_hash, f"{evasion}%"

# ────────────────────────────────────────────────
#   ZIP PROCESSING
# ────────────────────────────────────────────────

def process_zip(zip_path, intensity, add_debug, sarcastic, inconsistent, personal_names, redundancies, ref_code):
    ref_fingerprint = compute_style_fingerprint(ref_code) if ref_code else None

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = os.path.join(tmp_dir, "humanized")
        os.makedirs(output_dir)

        with zipfile.ZipFile(zip_path, 'r') as zin:
            zin.extractall(tmp_dir)

        for root, _, files in os.walk(tmp_dir):
            for file in files:
                if Path(file).suffix in SUPPORTED_EXTS:
                    in_path = os.path.join(root, file)
                    with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()

                    humanized, _, _, _ = humanize_code(code, intensity, add_debug, sarcastic, inconsistent, personal_names, redundancies, ref_fingerprint)

                    rel_path = os.path.relpath(in_path, tmp_dir)
                    out_path = os.path.join(output_dir, rel_path)
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(humanized)

        output_zip = os.path.join(tmp_dir, "humanized_output.zip")
        shutil.make_archive(output_zip[:-4], 'zip', output_dir)

        return output_zip

# ────────────────────────────────────────────────
#   PRESETS (same as Phase 1)
# ────────────────────────────────────────────────

def apply_preset(preset):
    if preset == "Burned-out Senior":
        return 7, True, True, True, True, True
    elif preset == "Enterprise Corporate":
        return 4, False, False, False, True, True
    elif preset == "Junior Enthusiast":
        return 6, True, True, True, False, False
    elif preset == "Minimal Clean Human":
        return 3, False, False, True, True, False
    elif preset == "Aggressive Undetectable":
        return 9, True, True, True, True, True
    else:
        return 5, True, True, True, True, False

# ────────────────────────────────────────────────
#   Gradio INTERFACE
# ────────────────────────────────────────────────

custom_css = """
body { background: linear-gradient(135deg, #0a0015, #1a0033); color: #00ff9d; font-family: 'Courier New', monospace; }
.gradio-container { border: 2px solid #00ff9d; border-radius: 12px; background: rgba(5,5,25,0.85); max-width: 1200px; margin: auto; padding: 1rem; }
h1, h2 { color: #00ff9d; text-shadow: 0 0 12px #00ff9d; }
button { background: #00ff9d !important; color: black !important; border: none; border-radius: 6px; font-weight: bold; }
button:hover { box-shadow: 0 0 18px #00ff9d; }
.output-badge { font-weight: bold; padding: 6px 12px; border-radius: 6px; }
.success { background: #00cc66; color: black; }
.warning { background: #ffaa00; color: black; }
.danger { background: #ff4444; color: white; }
"""

with gr.Blocks(css=custom_css, title="VATA Soul Check – Phase 2") as demo:
    gr.Markdown("# VATA Soul Check 2026 – Phase 2: Multi-File + Style Blending")
    gr.Markdown("Upload zip or paste code. Optional reference code to match your style. Outputs humanized zip + evasion estimate.")

    with gr.Tab("Humanizer (Make it Human)"):
        with gr.Row():
            input_mode = gr.Radio(["Single Code", "Zip File"], value="Single Code", label="Input Mode")

        code_in_h = gr.Textbox(lines=12, label="Paste Code (Single mode)", visible=True)
        zip_in = gr.File(label="Upload Zip (Multi-file mode)", file_types=[".zip"], visible=False)

        ref_code = gr.Textbox(lines=8, label="Optional: Reference Human Code (paste snippet or full file to match style)", placeholder="Paste your own human-written code here for fingerprinting...")

        with gr.Row():
            preset_dropdown = gr.Dropdown(
                choices=["Custom", "Burned-out Senior", "Enterprise Corporate", "Junior Enthusiast", "Minimal Clean Human", "Aggressive Undetectable"],
                value="Custom", label="Preset Persona"
            )
            intensity = gr.Slider(1, 10, value=5, step=1, label="Intensity")

        with gr.Row():
            add_debug = gr.Checkbox(label="Add debug prints/logs", value=True)
            sarcastic = gr.Checkbox(label="Sarcastic / personal comments", value=True)
            inconsistent = gr.Checkbox(label="Inconsistent formatting", value=True)
            personal_names = gr.Checkbox(label="Personal / quirky variable names", value=True)
            redundancies = gr.Checkbox(label="Harmless redundancies", value=False)

        humanize_btn = gr.Button("Humanize + Analyze", variant="primary")

        humanized_out = gr.Textbox(lines=10, label="Humanized Result (single mode)", interactive=False)
        download_zip = gr.File(label="Download Humanized Zip (multi mode)", interactive=False)

        with gr.Row():
            original_score = gr.Textbox(label="Original Score")
            humanized_score = gr.Textbox(label="Humanized Score")
            evasion_conf = gr.Textbox(label="Est. Evasion Confidence")
            delta_badge = gr.HTML(label="Improvement")

        # Toggle input mode
        def toggle_input(mode):
            return (
                gr.update(visible=mode == "Single Code"),
                gr.update(visible=mode == "Zip File")
            )

        input_mode.change(toggle_input, input_mode, [code_in_h, zip_in])

        # Preset update (same)
        preset_dropdown.change(
            apply_preset,
            preset_dropdown,
            [intensity, add_debug, sarcastic, inconsistent, personal_names, redundancies]
        )

        def run_humanize(mode, code, zip_file, ref, intensity_val, debug_val, sarc_val, inc_val, names_val, red_val):
            ref_fp = compute_style_fingerprint(ref) if ref else None

            if mode == "Single Code":
                if not code.strip():
                    return "", "", "0%", "0%", "0%", "<span class='output-badge danger'>No input</span>"
                humanized, h_score, _, evasion = humanize_code(code, intensity_val, debug_val, sarc_val, inc_val, names_val, red_val, ref_fp)
                o_score, _, _, _, _, _ = calculate_soul_score(code)
                delta = int(h_score.rstrip("%")) - int(o_score.rstrip("%"))
                badge = f"<span class='output-badge {'success' if delta > 20 else 'warning' if delta > 5 else 'danger'}'>{delta:+}%</span>"
                return humanized, "", o_score, h_score, evasion, badge

            else:  # Zip mode
                if not zip_file:
                    return "", "", "0%", "0%", "0%", "<span class='output-badge danger'>No zip</span>"
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                        shutil.copyfileobj(zip_file, tmp)
                        tmp_path = tmp.name
                    out_zip = process_zip(tmp_path, intensity_val, debug_val, sarc_val, inc_val, names_val, red_val, ref)
                    os.unlink(tmp_path)
                    return "Multi-file processed – see download", out_zip, "N/A (multi)", "N/A (multi)", "N/A (multi)", "<span class='output-badge success'>Zip ready</span>"
                except Exception as e:
                    return f"Error: {str(e)}", "", "Error", "Error", "Error", "<span class='output-badge danger'>Failed</span>"

        humanize_btn.click(
            run_humanize,
            [input_mode, code_in_h, zip_in, ref_code, intensity, add_debug, sarcastic, inconsistent, personal_names, redundancies],
            [humanized_out, download_zip, original_score, humanized_score, evasion_conf, delta_badge]
        )

    gr.Markdown("Phase 2 – Multi-file zip + Reference style blending | Built by @Lhmisme | 2026")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)



               