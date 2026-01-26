# souldetector.py (with ensemble/uncertainty)
import pickle
import numpy as np
from features import extract_features

MODEL_PATH = "soul_model_v1.pkl"
FEATURE_ORDER = [
    "line_count", "char_count", "avg_line_length", "comment_ratio", "has_todo", "comment_entropy",
    "comment_relevance", "ast_node_count", "ast_max_depth", "ast_branching_factor",
    "perplexity", "var_name_entropy", "var_pattern_ratio", "codebert_mean"
]  # Full list from features.py

def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def rule_based_fallback(features: dict) -> float:
    # Simple rules: penalize if high pattern/low relevance
    score = 50
    if features["comment_relevance"] < 0.3: score -= 20
    if features["var_pattern_ratio"] > 0.5: score -= 15
    return max(0, min(100, score))

def get_soul_score(code: str, language="python") -> dict:
    features_dict = extract_features(code, language)
    X = np.array([features_dict.get(k, 0) for k in FEATURE_ORDER]).reshape(1, -1)
    model = load_model()
    prob_human = model.predict_proba(X)[0][1]
    soul_score = prob_human * 100

    # Uncertainty: proba confidence + feature variance
    confidence = max(prob_human, 1 - prob_human) * 100  # High if decisive
    feature_var = np.var(X.flatten())  # Low var = bland/gamed?

    # Ensemble: avg with fallback
    fallback_score = rule_based_fallback(features_dict)
    ensemble_score = (soul_score + fallback_score) / 2

    gaming_risk = "low"
    if confidence < 70 or feature_var < 0.1:
        gaming_risk = "high"  # Flag potential manipulation

    return {
        "soul_score": round(ensemble_score, 2),
        "confidence": round(confidence, 2),
        "gaming_risk": gaming_risk
    }