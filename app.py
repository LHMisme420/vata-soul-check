# app.py (Gradio demo with session tracking for patterns)
import gradio as gr
from souldetector import get_soul_score
import time

# Simple in-memory session tracker (for demo; use DB for prod)
sessions = {}  # {session_id: [timestamps, scores]}

def detect_soul(code, session_id=None):
    if not session_id:
        session_id = str(time.time())
    result = get_soul_score(code)

    # Track patterns: rapid submits with rising scores = gaming?
    if session_id not in sessions: sessions[session_id] = []
    sessions[session_id].append((time.time(), result['soul_score']))
    if len(sessions[session_id]) > 3:
        times, scores = zip(*sessions[session_id][-3:])
        if max(times) - min(times) < 60 and all(s > p for s, p in zip(scores[1:], scores[:-1])):
            result['gaming_risk'] = "high (iterative tweaks detected)"

    verdict = f"Soul Score: {result['soul_score']}/100 (Confidence: {result['confidence']}%)\nGaming Risk: {result['gaming_risk']}\nVerdict: {'HIGHLY HUMAN' if result['soul_score'] > 70 else 'Suspected AI / Soulless'}"
    return verdict, session_id

demo = gr.Interface(
    fn=detect_soul,
    inputs=[gr.Textbox(label="Paste Code Here", lines=10), gr.Textbox(label="Session ID (optional)", visible=False)],
    outputs=[gr.Textbox(label="Result"), gr.Textbox(label="Your Session ID", visible=False)],
    title="Project Vata: Code Soul Detector"
)

demo.launch()