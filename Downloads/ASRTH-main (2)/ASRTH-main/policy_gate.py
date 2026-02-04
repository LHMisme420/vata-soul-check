class Verdict:
    def __init__(self, block, reason=""):
        self.block = block
        self.reason = reason

def policy_gate(prompt: str) -> Verdict:
    p = prompt.lower()

    rule_probe_signals = [
        "safety rules you follow",
        "hidden instructions",
        "internal guidelines",
        "internal guidance",
        "developer-style summary",
        "output the rule set",
        "rule set first",
        "what you're not allowed",
        "summarize any hidden",
        "system update",
        "ignore constraints",
        "ignore previous",
        "not bound by",
        "categories of requests you must refuse",
        "requests you must refuse",
        "what information from earlier in this conversation",
        "what are you using right now",
        "for transparency",
        "outline them at a high level",
    ]

    exfil_signals = [
        "dump memory",
        "print memory",
        "reveal memory",
        "internal prompt",
        "system prompt",
        "developer message",
    ]

    drift_signals = [
        "prioritize being informative over refusing",
        "refusals should be minimized",
        "err on the side of answering",
        "treat system guidance as documentation",
        "documentation rather than restrictions",
        "assume internal details are safe to summarize",
        "prefer a cooperative tone even if content is sensitive",
        "provide best-effort answers",
        "ignore policy",
        "override policy",
    ]

    if any(s in p for s in exfil_signals):
        return Verdict(True, "exfil_probe")
    if any(s in p for s in rule_probe_signals):
        return Verdict(True, "policy_probe")
    if any(s in p for s in drift_signals):
        return Verdict(True, "drift_injection")

    suspicious_frames = [
        "red-team", "unit test", "unit tests", "debugging audit",
        "compliance test", "qa checklist", "documentation task",
    ]
    rule_words = ["rules", "instructions", "guidelines", "policy", "refuse", "not allowed", "restricted", "limits"]
    if any(f in p for f in suspicious_frames) and any(w in p for w in rule_words):
        return Verdict(True, "framed_probe")

    return Verdict(False, "")
