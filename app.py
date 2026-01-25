import gradio as gr
import re
import random
import statistics
import hashlib
import time
import requests
import json
from collections import Counter

# ────────────────────────────────────────────────
#   LANGUAGE & COMMENT HELPERS (unchanged)
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
#   ANALYZER (unchanged)
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
#   RULE-BASED HUMANIZER (fast, deterministic)
# ────────────────────────────────────────────────

def rule_based_humanize(
    code: str,
    intensity: float,
    comment_int: float,
    debug_int: float,
    sarcasm_int: float,
    incon_int: float,
    rename_int: float,
    redund_int: float,
    comment_preset: str,
    naming_style: str,
    debug_prefix: str,
    lang_override: str
):
    if not code.strip():
        return code

    lang = lang_override if lang_override != "Auto" else detect_language(code)
    single = get_comment_styles(lang)["single"]

    lines = code.splitlines()
    new_lines = lines[:]

    intensities = {
        'comment': comment_int / 10,
        'debug': debug_int / 10,
        'sarcasm': sarcasm_int / 10,
        'inconsistency': incon_int / 10,
        'rename': rename_int / 10,
        'redundancy': redund_int / 10
    }

    comment_pools = {
        "Casual": ['TODO: revisit later', 'maybe fix this someday', 'works for now', 'borrowed idea', 'not proud of this'],
        "Professional": ['Refactor opportunity', 'Consider extracting method', 'Documentation pending', 'Temporary solution', 'Needs review'],
        "Sarcastic": ['why do we even...', 'future me hates me', 'send help', 'enterprise quality™', 'this is fine.jpg'],
        "Minimal": ['todo', 'fixme', 'note', 'debug']
    }
    comments_list = comment_pools.get(comment_preset, comment_pools["Casual"])

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
    humanized += f"\n\n# VATA Rule-based Humanized – hash {short_hash} – intensity {intensity:.1f}"

    return humanized

# ────────────────────────────────────────────────
#   LLM BLENDING PASS (optional second stage)
# ────────────────────────────────────────────────

def llm_blend_code(code: str, api_key: str, model: str = "grok-beta"):
    if not api_key.strip():
        return code + "\n\n# LLM blending skipped: no API key provided"

    prompt = f"""You are an expert senior developer with 12+ years of experience who writes clean but slightly imperfect, human-feeling code.

Take the following code that has already been lightly humanized with comments, debug statements, inconsistencies, etc.

Your task is to **refine it further** so it looks 100% like real hand-written code from a competent but busy mid/senior developer:

- Keep the logic 100% identical — no functional changes, no new bugs
- Make comments more natural/personal (some helpful, some sarcastic/joking, some "TODO" style)
- Add or adjust debug prints/logs that a human might leave temporarily
- Vary naming slightly (mix camelCase/snake_case, add personal abbreviations)
- Introduce tiny harmless redundancies (extra temp var, unnecessary else after return, etc.)
- Keep it readable and professional overall — not sloppy beginner code
- Aim for "this was written by a real person in a hurry, but knows what they're doing"

Input code:
```python
{code}