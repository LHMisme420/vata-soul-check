import sys
import gradio as gr
import os
import traceback
import warnings

# Suppress some common warnings from old dependencies
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
except ImportError as e:
    print(f"CRITICAL: Missing required packages - {e}")
    print("Run: pip install numpy pandas xgboost transformers torch")
    raise

# ======================
#  CONFIG & PATHS
# ======================
MODEL_PATH = "models/xgboost_soul_model.json"          # adjust if needed
PERPLEXITY_MODEL = "microsoft/codebert-base"           # or your preferred model

# Load tokenizer & model for perplexity (lazy load)
_perplexity_tokenizer = None
_perplexity_model = None

def load_perplexity_model():
    global _perplexity_tokenizer, _perplexity_model
    if _perplexity_tokenizer is None:
        print("Loading CodeBERT for perplexity calculation...")
        _perplexity_tokenizer = AutoTokenizer.from_pretrained(PERPLEXITY_MODEL)
        _perplexity_model = AutoModelForSequenceClassification.from_pretrained(PERPLEXITY_MODEL)
    return _perplexity_tokenizer, _perplexity_model

# Dummy / placeholder functions → replace with your real logic
def extract_features(code: str) -> dict:
    """Your original feature extraction logic goes here"""
    try:
        length = len(code)
        has_comment = "#" in code or "//" in code
        has_todo = "TODO" in code.upper()
        
        # Very naive perplexity simulation (replace with real calculation)
        tokenizer, model = load_perplexity_model()
        inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        perplexity = float(outputs.logits.abs().mean()) * 10  # dummy value
        
        return {
            "length": length,
            "comment_entropy": 3.14 if has_comment else 0.0,  # placeholder
            "perplexity": perplexity,
            "has_todo": 1 if has_todo else 0,
            "risky_commands": 0,  # placeholder
        }
    except Exception as e:
        print(f"Feature extraction failed: {e}")
        return {"error": str(e)}

def score_soul(features: dict) -> tuple[float, str]:
    """Your XGBoost scoring logic"""
    try:
        if "error" in features:
            return 0.0, "Feature extraction failed"

        # Very minimal dummy model simulation (replace with real loading)
        if not os.path.exists(MODEL_PATH):
            print(f"Warning: Model file not found at {MODEL_PATH} → using dummy score")
            score = 42.0 + features.get("has_todo", 0) * 20
        else:
            # Real loading example (uncomment when you have the model)
            # model = xgb.XGBClassifier()
            # model.load_model(MODEL_PATH)
            # X = pd.DataFrame([features])
            # score = model.predict_proba(X)[0][1] * 100
            score = 55.0  # dummy

        status = "Soulless Void" if score < 30 else "Low Soul" if score < 60 else "Human-ish" if score < 85 else "Vata Full Soul"
        return round(score, 1), status
    except Exception as e:
        traceback.print_exc()
        return 0.0, f"Scoring error: {str(e)}"

def analyze_soul(code: str, grok_api_key: str = ""):
    """
    Main function called by Gradio
    Returns: (status_message, humanized_code, detailed_log)
    """
    if not code or not code.strip():
        return "Please paste some actual code.", "", "Input is empty"

    if len(code) > 30000:
        return "Code too long (max ~30k characters)", "", "Input too large"

    try:
        features = extract_features(code)
        score, status = score_soul(features)

        humanized = ""
        if grok_api_key.strip():
            humanized = f"# Grok polishing requested (API key provided)\n# (real call not implemented yet)\n{code}\n# Add chaos + personality here"

        detailed = f"""Soul Score: {score}/100
Status: {status}
Features extracted:
{features}
"""
        return f"{status} ({score}%)", humanized or code, detailed

    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return "Analysis crashed", "", f"ERROR:\n{str(e)}\n\n{tb}"

# ======================
#  GRADIO INTERFACE
# ======================
with gr.Blocks(title="VATA Soul Check & Humanizer") as demo:

    gr.Markdown("""
    # VATA - Code Soul Scanner & Humanizer 🔥🪬

    Paste code → **Analyze Soul & Humanize** → get soul score + (optional) polished version.
    """)

    with gr.Row():
        with gr.Column(scale=2):
            input_code = gr.Textbox(
                label="Input Code (paste your script)",
                lines=12,
                placeholder="def soul_check(code): ... # TODO: add more chaos",
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
            status_output = gr.Textbox(label="Status", lines=8, interactive=False)

    humanized_output = gr.Textbox(label="Humanized / Polished Code", lines=10)

    with gr.Row():
        api_key = gr.Textbox(
            label="xAI Grok API Key (optional – for extra LLM soul polish)",
            placeholder="gsk_...",
            type="password",
            scale=1
        )

    gr.Markdown("---")

    analyze_btn = gr.Button("Analyze Soul & Humanize 🔥", variant="primary", scale=0)

    # Wire everything
    analyze_btn.click(
        fn=analyze_soul,
        inputs=[input_code, api_key],
        outputs=[status_output, humanized_output, gr.State()]  # last one can be hidden log
    )

    # Also trigger on Shift+Enter
    input_code.submit(
        fn=analyze_soul,
        inputs=[input_code, api_key],
        outputs=[status_output, humanized_output, gr.State()]
    )

if __name__ == "__main__":
    print("Starting VATA Soul Check ...")
    print(f"Python: {sys.version}")
    print(f"Torch: {torch.__version__ if 'torch' in globals() else 'not imported'}")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,          # change to True only for temporary public link
        debug=False
    )