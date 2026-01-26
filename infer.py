# infer.py (with gaming warning)
import argparse
from souldetector import get_soul_score

parser = argparse.ArgumentParser()
parser.add_argument("--code", type=str, required=True, help="Code snippet to score")
args = parser.parse_args()

result = get_soul_score(args.code)
print(f"Soul Score: {result['soul_score']}/100 (Confidence: {result['confidence']}%)")
print(f"Gaming Risk: {result['gaming_risk']}")
print("Verdict:", "HIGHLY HUMAN" if result['soul_score'] > 70 else "Suspected AI / Soulless")
if result['gaming_risk'] == "high":
    print("Warning: Possible gaming detected - score may be inflated.")