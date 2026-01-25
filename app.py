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
#   ANALYZER – SOUL SCORE
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
    exclude = {
        'def', 'if', 'for', 'return', 'else', 'True', 'False', 'None', 'self',
        'const', 'let', 'var', 'public', 'private', 'protected', 'static',
        'void', 'final', 'using', 'namespace', 'async', 'await'
    }
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
    if lang in ("java", "javascript", "cpp", "csharp"):
        nesting_proxy = indent_nesting + abs(brace_nesting) * 2
    else:
        nesting_proxy = indent_nesting
    complexity_bonus = min((branches * 3 + nesting_proxy * 2), 40)

    total_bonus = comment_bonus + naming_bonus + complexity_bonus

    stripped_lines = [l.strip() for l in lines if l.strip()]
    dup_ratio = (
        sum(c > 1 for c in Counter(stripped_lines).values()) /
        max(len(stripped_lines), 1)
        if stripped_lines else 0
    )
    repetition_penalty = dup_ratio * -60

    line_lengths = [len(l) for l in non_empty]
    len_std = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0
    simplicity_penalty = -max(0, 30 - len_std * 1.5)

    risky = 0
    lower = code.lower()
    dangerous_base = [
        "eval(", "exec(", "os.system(", "subprocess.", "pickle.load",
        "rm -rf", "format c:", "del *.*"
    ]
    dangerous_java = [
        "runtime.getruntime().exec(", "processbuilder(",
        "system.setsecuritymanager(null)", "thread.sleep(", "reflection"
    ] if lang == "java" else []
    dangerous_csharp = [
        "process.start(", "system.diagnostics.process(",
        "file.delete(", "directory.delete(", "thread.sleep(", "reflection"
    ] if lang == "csharp" else []
    secrets = ["password =", "api_key =", "secret =", "token =", "key =", "hardcoded"]
    bare_except_py = (
        len(re.findall(r'except\s*(?::|\))', code)) +
        len(re.findall(r'except\s+[A-Za-z]+\s*:', code))
    ) > 3
    bare_catch = (
        len(re.findall(r'\}\s*catch\s*\(\s*Exception\s*\w*\)\s*\{', code)) > 1
        if lang in ("java", "csharp") else 0
    )
    risky += sum(lower.count(pat) for pat in dangerous_base + dangerous_java + dangerous_csharp + secrets)
    risky += (bare_except_py + bare_catch) * 2
    risk_penalty = risky * -25

    total_penalty = repetition_penalty + simplicity_penalty + risk_penalty

    score = 45 + total_bonus + total_penalty
    score = max(5, min(98, round(score)))
    score_str = f"{score}%"

    if score >= 82:
        energy = "Vata Full Soul 🔥"
    elif score >= 65:
        energy = "Strong Vata Pulse ⚡"
    elif score >= 45:
        energy = "Hybrid Aura 🌫️"
    else:
        energy = "Soulless Void 🕳️"

    if score > 78:
        cls = "HUMAN"
    elif score > 50:
        cls = "MACHINE / HYBRID"
    else:
        cls = "AI-TRACED"

    if score >= 78 and risky <= 1:
        verdict = "VATA APPROVED ✅"
    elif score >= 45:
        verdict = "VATA FLAGGED ⚠️"
    else:
        verdict = "VATA REJECTED ❌"

    if risky >= 3:
        verdict = "VATA BLOCKED - SECURITY VIOLATIONS ⛔"

    if score >= 90:
        tier = "S+ Trusted Artisan"
    elif score >= 78:
        tier = "S Solid Human"
    elif score >= 62:
        tier = "A Probable Safe"
    elif score >= 45:
        tier = "B Needs Eyes"
    else:
        tier = "C High Risk"

    return score_str, energy, cls, verdict, tier