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
# LANGUAGE & COMMENT HELPERS
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
    if re.search(r'\b(#include|<.*?>|std::|cout|cin)\b', code_lower):
        return "cpp"
    return "other"

def get_comment_styles(lang: str):
    styles = {
        "python": {"single": "#"},
        "javascript": {"single": "//"},
        "java": {"single": "//"},
        "csharp": {"single": "//"},
        "cpp": {"single": "//"},
        "other": {"single": "//"}
    }
    return styles.get(lang, styles["other"])

# ────────────────────────────────────────────────
# ANALYZER – SOUL SCORE + BREAKDOWN
# ────────────────────────────────────────────────

def calculate_soul_score(code: str):
    if not code.strip():
        return "0%", "Empty", "NO CODE", "REJECTED", "Tier X - Invalid", {
            "comments": 0, "naming": 0, "complexplexity": 0,
            "repetition_penalty": 0, "simplicity_penalty": 0, "risk_penalty": 0,
        }

    lang = detect_language(code)
    lines = code.splitlines()
    non_empty = [l.strip() for l in lines if l.strip()]

    comments = sum(1 for l in lines if l.strip().startswith(('#', '//', '/\*', '\*')))
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
    len_std = statistics.stdev(line_lengths) if line_lengths > 1 else 0
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
        energy = "Hybrid Aura ⚖️"
    else:
        energy = "Soulless Void 👻"

    if score > 78:
        cls = "HUMAN"
    elif score > 50:
        cls = "MACHINE / HYBRID"
    else:
        cls = "AI-TRACED"

    if score >= 78 and risky <= 1:
        verdict = "VATA APPROVED"
    elif score >= 45:
        verdict = "VATA FLAGGED"
    else:
        verdict = "VATA REJECTED"

    if risky >= 3:
        verdict = "VATA BLOCKED - SECURITY VIOLATIONS"

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
        "complexplexity": round(complexity_bonus, 2),
        "repetition_penalty": round(repetition_penalty, 2),
        "simplicity_penalty": round(simplicity_penalty, 2),
        "risk_penalty": round(risk_penalty, 2),
    }

    return score_str, energy, cls, verdict, tier, breakdown, lang

# ────────────────────────────────────────────────
# RULE-BASED HUMANIZER
# ────────────────────────────────────────────────

def rule_based_humanize(
    code,
    intensity=5,
    comment_intensity=5,
    debug_intensity=3,
    sarcasm_intensity=4,
    inconsistency_intensity=2,
    rename_intensity=3,
    redundancy_intensity=2,
    comment_style_preset="Casual",
    naming_style="Mixed",
    debug_prefix="DEBUG:",
    language_override="Auto"
):
    if not code.strip():
        return code

    lang = language_override if language_override and language_override != "Auto" else detect_language(code)
    styles = get_comment_styles(lang)
    single = styles["single"]

    lines = code.splitlines()
    new_lines = []

    casual_comments = [
        "quick hack, works for now",
        "TODO: clean this up later",
        "not proud of this, but it works",
        "leaving this as-is for now"
    ]
    professional_comments = [
        "Validate input parameters.",
        "Handle edge cases and error conditions.",
        "Optimize this path if it becomes a bottleneck.",
        "Refactor into smaller functions if this grows."
    ]
    sarcastic_comments = [
        "if this breaks, future me will cry",
        "magic happens here, don't touch",
        "yes, this is intentional. probably.",
        "here be dragons"
    ]

    if comment_style_preset == "Casual":
        comment_pool = casual_comments
    elif comment_style_preset == "Professional":
        comment_pool = professional_comments
    elif comment_style_preset == "Sarcastic":
        comment_pool = sarcastic_comments
    else:
        comment_pool = casual_comments + professional_comments + sarcastic_comments

    comment_prob = min(max(comment_intensity / 10.0, 0.0), 1.0)
    debug_prob = min(max(debug_intensity / 10.0, 0.0), 1.0)
    redundancy_prob = min(max(redundancy_intensity / 10.0, 0.0), 1.0)
    inconsistency_prob = min(max(inconsistency_intensity / 10.0, 0.0), 1.0)

    for idx, line in enumerate(lines):
        stripped = line.strip()
        new_line = line

        if stripped and random.random() < inconsistency_prob * 0.3:
            if " " not in new_line:
                new_line = new_line.replace(" ", "  ", 1)  # small inconsistency

        new_lines.append(new_line)

        if stripped and not stripped.startswith(single) and random.random() < comment_prob * 0.4:
            comment_text = random.choice(comment_pool)
            if sarcasm_intensity > 5 and random.random() < 0.4:
                comment_text = random.choice(sarcastic_comments)
            new_lines.insert(len(new_lines) - 1, single + " " + comment_text)

        if stripped and any(k in stripped for k in ["=", "return", "if ", "for ", "while "]) and random.random() < debug_prob * 0.3:
            indent = len(line) - len(line.lstrip())
            if lang == "python":
                dbg = f"print('{debug_prefix} line {idx + 1}')"
            else:
                dbg = single + f" {debug_prefix} line {idx + 1}"
            new_lines.append(" " * indent + dbg)

        if stripped.startswith(single) and random.random() < redundancy_prob * 0.2:
            new_lines.append(new_line)  # duplicate comment sometimes

    return "\n".join(new_lines)

# ────────────────────────────────────────────────
# GROK API WRAPPER
# ────────────────────────────────────────────────

def call_grok_api(prompt, api_key, model="grok-beta", max_retries=2, timeout=30):
    if not api_key or not api_key.strip():
        return None, "No API key provided - skipping LLM enhancement"

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a senior software engineer who writes realistic, human-feeling code with natural imperfections, personal comments, and soul."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }

    last_error = None
    for _ in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(1.5)
                continue
            data = resp.json()
            return data["choices"][0]["message"]["content"], None
        except Exception as e:
            last_error = str(e)
            time.sleep(1.5)

    return None, f"Grok API failed after retries: {last_error}"

# ────────────────────────────────────────────────
# MAIN PROCESSING FUNCTION
# ────────────────────────────────────────────────

def process_code(
    code,
    api_key,
    overall_intensity=5,
    comment_intensity=5,
    debug_intensity=3,
    sarcasm_intensity=4,
    inconsistency_intensity=2,
    rename_intensity=3,
    redundancy_intensity=2,
    comment_style="Casual",
    naming_style="Mixed",
    debug_prefix="DEBUG:",
    lang_override="Auto"
):
    if not code.strip():
        return "**No code entered.** Paste some soulful chaos!", ""

    score_str, energy, cls, verdict, tier, breakdown, detected_lang = calculate_soul_score(code)

    humanized = rule_based_humanize(
        code,
        intensity=overall_intensity,
        comment_intensity=comment_intensity,
        debug_intensity=debug_intensity,
        sarcasm_intensity=sarcasm_intensity,
        inconsistency_intensity=inconsistency_intensity,
        rename_intensity=rename_intensity,
        redundancy_intensity=redundancy_intensity,
        comment_style_preset=comment_style,
        naming_style=naming_style,
        debug_prefix=debug_prefix,
        language_override=lang_override
    )

    # Optional LLM polish if key provided
    llm_result = ""
    if api_key and api_key.strip():
        llm_prompt = (
            f"Take this already lightly humanized code and make it feel even more authentically human-written:\n"
            f"Add subtle imperfections, varied style, personal touches, maybe a funny or thoughtful comment.\n"
            f"Keep the logic intact.\n\nCode:\n``` \n{humanized}\n```"
        )
        enhanced, err = call_grok_api(llm_prompt, api_key)
        if enhanced:
            humanized = enhanced.strip()
            llm_result = "\n**LLM Polish applied via Grok** (extra soul infusion) ✨"
        else:
            llm_result = f"\n**LLM skipped/error:** {err}"

    md_output = f"""
**Soul Score:** {score_str}  
**Energy:** {energy}  
**Classification:** {cls}  
**Verdict:** {verdict}  
**Tier:** {tier}  

**Breakdown:**  
- Comments bonus: +{breakdown['comments']}  
- Naming chaos: +{breakdown['naming']}  
- Complexity pulse: +{breakdown['complexplexity']}  
- Repetition penalty: {breakdown['repetition_penalty']}  
- Simplicity dock: {breakdown['simplicity_penalty']}  
- Risk flags: {breakdown['risk_penalty']}  

**Humanized Version (Rule-based + optional LLM):**  