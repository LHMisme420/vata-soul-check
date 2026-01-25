import gradio as gr
import os
import traceback
import warnings
import sys

# Suppress some common warnings from old dependencies
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
    print(f"CRITICAL: Missing required packages - {e}")
    print("Run: pip install numpy pandas xgboost transformers torch xai-sdk")
    raise

# ======================
#  CONFIG & PATHS
# ======================
MODEL_PATH = "models/xgboost_soul_model.json"          # adjust if needed
PERPLEXITY_MODEL = "microsoft/codebert-base"

_perplexity_tokenizer = None
_perplexity_model = None

def load_perplexity_model():
    global _perplexity_tokenizer, _perplexity_model
    if _perplexity_tokenizer is None:
        print("Loading CodeBERT for perplexity calculation...")
        _perplexity_tokenizer = AutoTokenizer.from_pretrained(PERPLEXITY_MODEL)
        _perplexity_model = AutoModelForSequenceClassification.from_pretrained(PERPLEXITY_MODEL)
    return _perplexity_tokenizer, _perplexity_model

# ======================
# FEATURE EXTRACTION (placeholder – improve later)
# ======================
def extract_features(code: str) -> dict:
    try:
        length = len(code)
        has_comment = "#" in code or "//" in code
        has_todo = "TODO" in code.upper()

        tokenizer, model = load_perplexity_model()
        inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        perplexity = float(outputs.logits.abs().mean()) * 10  # very naive placeholder

        return {
            "length": length,
            "comment_entropy": 3.14 if has_comment else 0.0,
            "perplexity": perplexity,
            "has_todo": 1 if has_todo else 0,
            "risky_commands": 0,
        }
    except Exception as e:
        print(f"Feature extraction failed: {e}")
        return {"error": str(e)}

# ======================
# SOUL SCORING (placeholder – improve later)
# ======================
def score_soul(features: dict) -> tuple[float, str]:
    if "error" in features:
        return 0.0, "Feature extraction failed"

    if not os.path.exists(MODEL_PATH):
        print(f"Warning: Model file not found at {MODEL_PATH} → using dummy score")
        score = 42.0 + features.get("has_todo", 0) * 20 + features.get("comment_entropy", 0) * 5
    else:
        # Uncomment when real model is ready
        # model = xgb.XGBClassifier()
        # model.load_model(MODEL_PATH)
        # X = pd.DataFrame([features])
        # score = model.predict_proba(X)[0][1] * 100
        score = 55.0 + features.get("has_todo", 0) * 15  # dummy

    status = "Soulless Void" if score < 30 else "Low Soul" if score < 60 else "Human-ish" if score < 85 else "Vata Full Soul"
    return round(score, 1), status

# ======================
# GROK HUMANIZER
# ======================
def humanize_with_grok(code: str, api_key: str) -> str:
    if not api_key.strip():
        return code + "\n\n# No xAI Grok API key provided → original code unchanged"

    print(f"[GROK] Attempting call with key prefix: {api_key[:6]}...")

    try:
        client = Client(api_key=api_key.strip(), timeout=120)

        # Try models in order of likely availability / capability (2026 situation)
        models_to_try = ["grok-beta", "grok-3-mini", "grok-4"]

        for model_name in models_to_try:
            try:
                print(f"[GROK] Trying model: {model_name}")
                chat = client.chat.create(model=model_name)

                chat.append(system(
                    "You are a quirky, passionate senior developer with real soul in your code. "
                    "Rewrite the provided code to feel authentically hand-written: add witty or sarcastic comments, "
                    "subtle imperfections, creative variable/function names where it makes sense, "
                    "a bit of personality or chaos, but keep it 100% functional and in the same language. "
                    "Output ONLY the rewritten code — no explanations, no markdown fences."
                ))

                chat.append(user(code))

                response = chat.sample(temperature=0.9, max_tokens=2000)
                result = response.content.strip()

                print(f"[GROK] Success with {model_name} — length: {len(result)} chars")
                if len(result) > 30:
                    return f"# Grok-polished ({model_name})\n{result}"

            except Exception as inner:
                print(f"[GROK] Model {model_name} failed: {str(inner)}")
                continue

        return code + "\n\n# All Grok models failed — check container logs for details"

    except Exception as e:
        msg = str(e).lower()
        hint = ""
        if any(x in msg for x in ["auth", "invalid", "key", "credential"]):
            hint = " → invalid or expired API key / check credits at console.x.ai"
        elif "rate" in msg or "limit" in msg or "quota" in msg:
            hint = " → rate limit or quota exceeded — wait and retry"
        elif "model" in msg or "not found" in msg:
            hint = " → model unavailable — try different key/tier"

        print(f"[GROK ERROR] {e}")
        return code + f"\n\n# Grok API call failed{hint}:\n{str(e)}"

# ======================
# MAIN ANALYZE FUNCTION
# ======================
def analyze_soul(code: str, grok_api_key: str = ""):
    if not code or not code.strip():
        return "Please paste some code.", "", "Input is empty"

    if len(code) > 30000:
        return "Code too long (max ~30k characters)", "", "Input too large"

    try:
        features = extract_features(code)
        score, status = score_soul(features)

        humanized = humanize_with_grok(code, grok_api_key)

        detailed = f"""Soul Score: {score}/100
Status: {status}
Features: {features}
Grok attempt: {'Yes' if grok_api_key.strip() else 'No'}"""

        return f"{status} ({score}%)", humanized, detailed

    except Exception as e:
        tb = traceback.format_exc()
        print("Analyze crashed:", tb)
        return "Analysis crashed", code, f"ERROR:\n{str(e)}\n\n{tb}"

# ======================
# GRADIO INTERFACE
# ======================
with gr.Blocks(title="VATA Soul Check & Humanizer") as demo:

    gr.Markdown("""
    # VATA - Code Soul Scanner & Humanizer 🔥🪬

    Paste code → Analyze → get soul score + (optional) Grok-polished version with more personality.
    Provide xAI Grok API key for real humanization (get key at https://console.x.ai).
    """)

    with gr.Row():
        with gr.Column(scale=2):
            input_code = gr.Textbox(
                label="Input Code (paste your script)",
                lines=12,
                placeholder="# Paste PowerShell / Python / JS here",
                value="""# Example PowerShell
function Get-Soul {
    param($code)
    Write-Output "Analyzing soul level..."
    # TODO: implement real chaos
}
Get-Soul -code $PSVersionTable
""",
            )

        with gr.Column(scale=1):
            status_output = gr.Textbox(label="Status & Score", lines=8, interactive=False)

    humanized_output = gr.Textbox(label="Humanized / Polished Code", lines=12)

    api_key = gr.Textbox(
        label="xAI Grok API Key (optional – for real soul polish)",
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
    print("Starting VATA Soul Check ...")
    print(f"Python: {sys.version}")
    print(f"Torch: {torch.__version__ if 'torch' in globals() else 'not imported'}")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False
    )