import gradio as gr
import os
import traceback
import warnings
import sys

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import numpy as np
    import pandas as pd
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    from xai_sdk import Client
    from xai_sdk.chat import user, system
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    print("Run: pip install numpy pandas transformers torch xai-sdk")
    raise

# ────────────────────────────────────────────────
# CONFIG & MODELS
# ────────────────────────────────────────────────

PERPLEXITY_MODEL = "microsoft/codebert-base"

_perplexity_tokenizer = None
_perplexity_model = None

def load_perplexity_model():
    global _perplexity_tokenizer, _perplexity_model
    if _perplexity_tokenizer is None:
        print("[PERPLEXITY] Loading CodeBERT...")
        _perplexity_tokenizer = AutoTokenizer.from_pretrained(PERPLEXITY_MODEL)
        _perplexity_model = AutoModelForSequenceClassification.from_pretrained(PERPLEXITY_MODEL)
    return _perplexity_tokenizer, _perplexity_model

# ────────────────────────────────────────────────
# FEATURE EXTRACTION
# ────────────────────────────────────────────────

def extract_features(code: str) -> dict:
    try:
        length = len(code)
        has_comment = "#" in code or "//" in code
        has_todo = "TODO" in code.upper()

        tokenizer, model = load_perplexity_model()
        inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        perplexity_proxy = float(outputs.logits.abs().mean()) * 10

        return {
            "length": length,
            "comment_entropy": 3.14 if has_comment else 0.0,
            "perplexity_proxy": perplexity_proxy,
            "has_todo": 1 if has_todo else 0,
            "risky_commands": 0,
        }
    except Exception as e:
        print(f"[FEATURES] Error: {e}")
        return {"error": str(e)}

# ────────────────────────────────────────────────
# SOUL SCORING – improved dummy version
# ────────────────────────────────────────────────

def score_soul(features: dict) -> tuple[float, str]:
    if "error" in features:
        return 0.0, "Feature extraction failed"

    score = 50.0
    score += features.get("has_todo", 0) * 25
    score += features.get("comment_entropy", 0) * 8
    score += min(features.get("perplexity_proxy", 0) / 8, 15)
    score -= max(0, (features.get("length", 0) - 500) / 100)

    score = max(0, min(100, score))

    status = (
        "Soulless Void" if score < 30 else
        "Low Soul"      if score < 60 else
        "Human-ish"     if score < 85 else
        "Vata Full Soul"
    )
    return round(score, 1), status

# ────────────────────────────────────────────────
# GROK HUMANIZER
# ────────────────────────────────────────────────

def humanize_with_grok(code: str, api_key: str) -> str:
    if not api_key.strip():
        return code + "\n\n# No xAI Grok API key provided"

    print(f"[GROK] Starting call | Key prefix: {api_key[:6]}...")

    try:
        client = Client(api_key=api_key.strip(), timeout=120)

        models_to_try = ["grok-beta", "grok-3-mini", "grok-4"]

        for model_name in models_to_try:
            try:
                print(f"[GROK] Trying: {model_name}")
                chat = client.chat.create(model=model_name)

                chat.append(system(
                    "You are a quirky, passionate senior developer with real soul in your code. "
                    "Rewrite the given code to feel authentically hand-written: add witty or sarcastic comments, "
                    "subtle imperfections, creative naming, artistic structure, a bit of chaos/flair. "
                    "Keep it 100% functional and in the same language. "
                    "Output ONLY the rewritten code — no explanations, no markdown fences."
                ))

                chat.append(user(code))

                response = chat.sample()
                result = response.content.strip()

                print(f"[GROK] Success with {model_name} — length: {len(result)}")
                if len(result) > 40:
                    return f"# Grok-polished ({model_name})\n{result}"

            except Exception as inner_e:
                print(f"[GROK] {model_name} failed: {str(inner_e)}")
                continue

        return code + "\n\n# All Grok models failed — check Logs tab for details"

    except Exception as e:
        msg = str(e).lower()
        hint = ""
        if any(w in msg for w in ["auth", "invalid", "key", "credential", "forbidden"]):
            hint = " → Check key validity / credits at https://console.x.ai"
        elif any(w in msg for w in ["rate", "limit", "quota", "429"]):
            hint = " → Rate limit — wait a few minutes"
        elif "model" in msg or "not found" in msg:
            hint = " → Model unavailable — try different key/tier"

        print(f"[GROK CRITICAL] {e}")
        return code + f"\n\n# Grok API failed{hint}:\n{str(e)}"

# ────────────────────────────────────────────────
# MAIN ANALYZE FUNCTION
# ────────────────────────────────────────────────

def analyze_soul(code: str, grok_api_key: str = ""):
    if not code.strip():
        return "<p style='text-align:center; color:grey; font-size:1.3em;'>Paste some code first.</p>", ""

    if len(code) > 30000:
        return "<p style='text-align:center; color:orange; font-size:1.3em;'>Code too long (max ~30k chars)!</p>", ""

    try:
        features = extract_features(code)
        score, status = score_soul(features)

        humanized = humanize_with_grok(code, grok_api_key)

        color = "red" if score < 30 else "orange" if score < 60 else "blue" if score < 85 else "green"
        score_visual = f"<h2 style='color:{color}; text-align:center; margin:20px 0; font-size:1.8em;'>{status} ({score}%)</h2>"

        return score_visual, humanized

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[CRASH] {tb}")
        return "<p style='text-align:center; color:red; font-size:1.3em;'>Crashed! Check logs.</p>", code

# ────────────────────────────────────────────────
# GRADIO UI
# ────────────────────────────────────────────────

with gr.Blocks(title="VATA Soul Check & Humanizer") as demo:
    gr.Markdown("""
    # VATA - Code Soul Scanner & Humanizer 🔥🪬

    Paste code → Analyze → soul score + optional Grok-polished version.  
    Add xAI Grok API key for real humanization (https://console.x.ai).
    """)

    gr.Examples(
        examples=[
            [
                """function Get-SystemInfo {
    param([string]$ComputerName = $env:COMPUTERNAME)
    Get-ComputerInfo -ComputerName $ComputerName |
        Select-Object WindowsProductName, OsVersion, CsManufacturer, CsModel
}
Get-SystemInfo""",
                "Clean AI-style PowerShell"
            ],
            [
                """# this kills zombie tabs dont @ me
Get-Process chrome | ? {$_.WorkingSet64 -gt 1GB} | % {
    "Murdering $($_.ProcessName) - $($_.WorkingSet64 / 1MB)MB"
    Stop-Process $_.Id -Force
}""",
                "Messy human-style PowerShell"
            ],
            [
                """def factorial(n):
    return 1 if n == 0 else n * factorial(n-1)

print(factorial(6))""",
                "Short Python recursive"
            ],
        ],
        inputs=gr.Textbox(lines=12, label="Input Code"),
        label="Try these examples"
    )

    with gr.Row():
        with gr.Column(scale=2):
            input_code = gr.Textbox(
                label="Input Code (paste your script)",
                lines=12,
                placeholder="# Paste PowerShell / Python / JS here",
            )

        with gr.Column(scale=1):
            status_output = gr.Markdown("**Status & Score**\nWaiting for input...", elem_id="score-display")

    humanized_output = gr.Textbox(label="Humanized / Polished Code (Grok if key provided)", lines=12)

    api_key = gr.Textbox(
        label="xAI Grok API Key (optional)",
        placeholder="xai-... or gsk_...",
        type="password",
    )

    analyze_btn = gr.Button("Analyze Soul & Humanize 🔥", variant="primary")

    analyze_btn.click(
        fn=analyze_soul,
        inputs=[input_code, api_key],
        outputs=[status_output, humanized_output]
    )

    input_code.submit(
        fn=analyze_soul,
        inputs=[input_code, api_key],
        outputs=[status_output, humanized_output]
    )

if __name__ == "__main__":
    print("=== VATA Soul Check starting ===")
    print(f"Python: {sys.version}")
    print(f"Torch: {torch.__version__ if 'torch' in globals() else 'N/A'}")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)