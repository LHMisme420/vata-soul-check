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
#   ANALYZER – SOUL SCORE + BREAKDOWN
# ────────────────────────────────────────────────

def calculate_soul_score(code: str):
    if not code.strip():
        return "0%", "Empty", "NO CODE", "REJECTED", "Tier X - Invalid", {
            "comments": 0,
            "naming": 0,
            "complexity": 0,
            "repetition_penalty": 0,
            "simplicity_penalty": 0,
            "risk_penalty": 0,
        }

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
        'void', 'final', 'using', 'namespace', 'async', 'await', 'class',
        'try', 'except', 'finally', 'catch', 'switch', 'case'
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

    total_bonus = comment_bonus + naming_bonus + complexity_bonus
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

    breakdown = {
        "comments": round(comment_bonus, 2),
        "naming": round(naming_bonus, 2),
        "complexity": round(complexity_bonus, 2),
        "repetition_penalty": round(repetition_penalty, 2),
        "simplicity_penalty": round(simplicity_penalty, 2),
        "risk_penalty": round(risk_penalty, 2),
    }

    return score_str, energy, cls, verdict, tier, breakdown

# ────────────────────────────────────────────────
#   RULE-BASED HUMANIZER
# ────────────────────────────────────────────────

def rule_based_humanize(
    code: str,
    intensity: float,
    comment_intensity: float,
    debug_intensity: float,
    sarcasm_intensity: float,
    inconsistency_intensity: float,
    rename_intensity: float,
    redundancy_intensity: float,
    comment_style_preset: str,
    naming_style: str,
    debug_prefix: str,
    language_override: str
) -> str:
    if not code.strip():
        return code

    if language_override and language_override != "Auto":
        lang = language_override
    else:
        lang = detect_language(code)

    styles = get_comment_styles(lang)
    single = styles["single"]

    lines = code.splitlines()
    new_lines = []

    # Comment pools
    casual_comments = [
        "quick hack, works for now",
        "TODO: clean this up later",
        "not proud of this, but it works",
        "leaving this as-is for now",
    ]
    professional_comments = [
        "Validate input parameters.",
        "Handle edge cases and error conditions.",
        "Optimize this path if it becomes a bottleneck.",
        "Refactor into smaller functions if this grows.",
    ]
    sarcastic_comments = [
        "if this breaks, future me will cry",
        "magic happens here, don't touch",
        "yes, this is intentional. probably.",
        "here be dragons",
    ]

    if comment_style_preset == "Casual":
        comment_pool = casual_comments
    elif comment_style_preset == "Professional":
        comment_pool = professional_comments
    elif comment_style_preset == "Sarcastic":
        comment_pool = sarcastic_comments
    else:
        comment_pool = casual_comments + professional_comments

    comment_prob = min(max(comment_intensity / 10.0, 0.0), 1.0)
    debug_prob = min(max(debug_intensity / 10.0, 0.0), 1.0)
    redundancy_prob = min(max(redundancy_intensity / 10.0, 0.0), 1.0)
    inconsistency_prob = min(max(inconsistency_intensity / 10.0, 0.0), 1.0)

    for idx, line in enumerate(lines):
        stripped = line.strip()
        new_line = line

        # Random minor spacing inconsistency
        if stripped and random.random() < inconsistency_prob * 0.3:
            if "  " not in new_line:
                new_line = new_line.replace(" ", "  ", 1)

        new_lines.append(new_line)

        # Insert comments above some non-empty lines
        if stripped and not stripped.startswith(single) and random.random() < comment_prob * 0.4:
            comment_text = random.choice(comment_pool)
            if sarcasm_intensity > 5 and random.random() < 0.4:
                comment_text = random.choice(sarcastic_comments)
            new_lines.insert(len(new_lines) - 1, f"{single} {comment_text}")

        # Insert debug prints after some lines that look like logic
        if stripped and any(k in stripped for k in ["=", "return", "if ", "for ", "while "]) and random.random() < debug_prob * 0.3:
            if lang == "python":
                dbg = f'print("{debug_prefix} line {idx+1}", {repr(stripped)})'
            elif lang in ("javascript", "java", "csharp", "cpp"):
                dbg = f'console.log("{debug_prefix} line {idx+1}");'
            else:
                dbg = f'{single} {debug_prefix} line {idx+1}'
            indent = len(line) - len(line.lstrip())
            new_lines.append(" " * indent + dbg)

        # Redundancy: duplicate harmless comment or blank-ish lines
        if stripped.startswith(single) and random.random() < redundancy_prob * 0.2:
            new_lines.append(new_line)

    humanized = "\n".join(new_lines)
    return humanized

# ────────────────────────────────────────────────
#   GROK API WRAPPER (XAI)
# ────────────────────────────────────────────────

def call_grok_api(prompt: str, api_key: str, model: str = "grok-beta", max_retries: int = 2, timeout: int = 30):
    if not api_key or not api_key.strip():
        return None, "No API key provided. Skipping LLM blend."

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a senior software engineer who writes realistic, human-feeling code."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 4096
    }

    last_error = None
    for _ in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
            if resp.status_code != 200:
                last_error = f"Grok API HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(1.0)
                continue
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content, None
        except Exception as e:
            last_error = str(e)
            time.sleep(1.0)

    return None, f"Grok API failed after retries: {last_error}"

# ────────────────────────────────────────────────
#   LLM BLENDING PASS – HYBRID
# ────────────────────────────────────────────────

def llm_blend_code(code: str, api_key: str, model: str = "grok-beta"):
    if not code.strip():
        return "# No code provided for LLM blending."

    if not api_key.strip():
        return code + "\n\n# LLM blending skipped: no API key provided"

    prompt_template = """
You are an expert senior developer with 12+ years of experience who writes clean but slightly imperfect, human-feeling code.
The input code has already been lightly humanized with comments, debug statements, inconsistencies, etc.

Your task:
- Keep the logic 100% identical — no functional changes, no new bugs.
- Preserve the overall structure but feel free to reorder small helper functions if it feels natural.
- Make comments more natural/personal (some helpful, some sarcastic/joking, some "TODO" style).
- Keep some of the existing humanizer artifacts (debug prints, TODOs, minor inconsistencies) so it still feels like a real person.
- Vary naming slightly (mix camelCase/snake_case, add personal abbreviations) but do NOT break references.
- Introduce tiny harmless redundancies (extra temp var, unnecessary else after return, etc.).
- Keep it readable and professional overall — not sloppy beginner code.
- Aim for: "this was written by a competent mid/senior dev in a hurry."

Return ONLY the final code, no explanation, no markdown fences.

Input code:
```python
{0}
 prompt = prompt_template.format(code)
blended, error = call_grok_api(prompt, api_key, model=model)
if error is not None or blended is None:
return code + f"\n\n# LLM blending failed or skipped: {error}"

return blended   