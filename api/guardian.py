import re
from typing import Tuple, List

PII_PATTERNS = [
    (r'\b\d{3}-\d{2}-\d{4}\b', "SSN"),
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "Email"),
    (r'\(\d{3}\)\s?\d{3}-\d{4}|\b\d{3}[-.]\d{3}[-.]\d{4}\b', "Phone"),
    (r'\b4[0-9]{12}(?:[0-9]{3})?\b', "Credit Card (Visa)"),
    (r'\b5[1-5][0-9]{14}\b', "Credit Card (Mastercard)"),
    (r'\b[A-Z]{2}\d{6}[A-Z]?\b', "Passport"),
]

def scan(text: str) -> Tuple[bool, List[str]]:
    if not text:
        return False, []
    findings = []
    for pattern, label in PII_PATTERNS:
        if re.search(pattern, str(text), re.IGNORECASE):
            findings.append(label)
    return len(findings) > 0, findings

def scan_signals(signals: list) -> Tuple[bool, List[str]]:
    all_findings = []
    for s in signals:
        found, findings = scan(str(s))
        if found:
            all_findings.extend(findings)
    return len(all_findings) > 0, all_findings

def guardian_check(signals: list) -> dict:
    found, findings = scan_signals(signals)
    return {
        "blocked": found,
        "findings": findings,
        "reason": ", ".join(findings) if findings else "Clean",
        "signal_count": len(signals)
    }
