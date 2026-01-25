import gradio as gr
import os
import traceback
import warnings
import sys

# Suppress noisy warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    from xai_sdk import Client
    from xai_sdk.chat import user, system
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    print("Install missing: pip install numpy pandas xgboost transformers torch xai-sdk")
    raise

# Config
MODEL_PATH = "models/xgboost_soul_model.json"  # your trained XGBoost model (if exists)
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

# Feature extraction (basic placeholder — expand later with real AST/entropy)
def extract_features(code: str) -> dict:
    try:
        length = len(code)
        has_comment = "#" in code or "//" in code
        has_todo = "TODO" in code.upper()

        tokenizer, model = load_perplexity_model()
        inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        perplexity = float(outputs.logits.abs().mean()) * 10  # naive proxy

        return {
            "length": length,
            "comment_entropy": 3.14 if has_comment else 0.0,
            "perplexity": perplexity,
            "has_todo": 1 if has_todo else 0,
            "risky_commands": 0,
        }
    except Exception as e:
        print(f"[FEATURES] Error: {e}")
        return {"error": str(e)}

# Soul scoring (placeholder until real model file is uploaded)
def score_soul(features: dict) -> tuple[float, str]:
    if "error" in features:
        return 0.0, "Feature extraction failed"

    if not os.path.exists(MODEL_PATH):
        print("[SCORE] No model file → using dummy logic")
        score = 50.0 + features.get("has_todo", 0) * 25 + features.get("comment_entropy", 0) * 5
    else:
        # Real XGBoost (uncomment when model exists)
        # model = xgb.XGBClassifier()
        # model.load_model(MODEL_PATH)
        # score = model.predict_proba(pd.DataFrame([features]))[0][1] * 100
        score = 65.0  # dummy fallback

    status = "Soulless Void" if score < 30 else "Low Soul" if score < 60 else "Human-ish" if score < 85 else "Vata Full Soul"
    return round(score, 1), status

# Real Grok humanization
def humanize_with_grok(code: str, api_key: str) -> str:
    if not api_key.strip():
        return code + "\n\n# No xAI Grok API key entered → original code kept"

    print(f"[GROK] Starting call | Key prefix: {api_key[:6]}...")

    try:
        client = Client(api_key=api_key.strip(), timeout=120)

        # Model order: prefer stable/available ones first (Jan 2026 reality)
        models_to_try = ["grok-beta", "grok-3-mini", "grok-4"]

        for model_name in models_to_try:
            try:
                print(f"[GROK] Trying: {model_name}")
                chat = client.chat.create(model=model_name)

                chat.append(system(
                    "You are a passionate, eccentric developer with real soul and personality in your code. "
                    "Rewrite the given code to feel hand-crafted: add witty/sarcastic comments, slight imperfections, "
                    "creative names, artistic structure, a dash of chaos/flair — but keep it fully functional "
                    "and in the original language. Output ONLY the rewritten code. No explanations, no fences."
                ))

                chat.append(user(code))

                response = chat.sample(temperature=0.9, max_tokens=2000)
                result = response.content.strip()

                print(f"[GROK] Success ({model_name}) — chars: {len(result)}")
                if len(result) > 40:
                    return f"# Grok-polished with {model_name}\n{result}"

            except Exception as inner_e:
                print(f"[GROK] {model_name} failed: {str(inner_e)}")
                continue

        return code + "\n\n# Grok failed on all models — check Logs tab for details"

    except Exception as e:
        msg = str(e).lower()
        hint = ""
        if any(k in msg for k in ["auth", "invalid", "key", "credential", "forbidden"]):
            hint = " → Check key validity / credits at https://console.x.ai"
        elif any(k in msg for k in ["rate", "limit", "quota", "429"]):
            hint = " → Rate limit — wait 1–5 min and retry"
        elif "model" in msg or "not found" in msg:
            hint = " → Model unavailable — try different key or tier"

        print(f"[GROK CRITICAL] {e}")
        return code + f"\n\n# Grok API failed{hint}:\n{str(e)}"

# Main logic
def analyze_soul(code: str, grok_api_key: str = ""):
    if not code.strip():
        return "Paste some code first.", "", "Empty input"

    if len(code) > 30000:
        return "Code too long!", "", "Over limit (~30k chars)"

    try:
        features = extract_features(code)
        score, status = score_soul(features)

        humanized = humanize_with_grok(code, grok_api_key)

        detailed = f"""Score: {score}/100 – {status}
Features: {features}
Grok: {'Attempted' if grok_api_key.strip() else 'Skipped'}"""

        return f"{status} ({score}%)", humanized, detailed

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ANALYZE CRASH] {tb}")
        return "Crashed 😢", code, f"ERROR:\n{str(e)}\n\n{tb}"

# Gradio UI
with gr.Blocks(title="VATA Soul Check & Humanizer") as demo:
    gr.Markdown("""
    # VATA - Code Soul Scanner & Humanizer 🔥🪬

    Paste code → Analyze → soul score + optional Grok-polished version.
    Add xAI Grok API key for real humanization (https://console.x.ai).
    """)

    with gr.Row():
        with gr.Column(scale=2):
            input_code = gr.Textbox(
                label="Input Code (paste your script)",
                lines=12,
                placeholder="# Paste PowerShell / Python etc here",
            )

        with gr.Column(scale=1):
            status_output = gr.Textbox(label="Status & Score", lines=8, interactive=False)

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