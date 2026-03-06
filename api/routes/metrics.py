from fastapi import APIRouter
from store.db import get_all_proofs, get_all_batches

router = APIRouter()

@router.get("/")
def get_metrics():
    proofs = get_all_proofs()
    batches = get_all_batches()
    total = len(proofs)
    valid = sum(1 for p in proofs if p.get("status") == "valid")
    gas_values = [p["gas_used"] for p in proofs if p.get("gas_used")]
    avg_gas = round(sum(gas_values) / len(gas_values)) if gas_values else 0
    return {
        "total_proofs": total,
        "valid_proofs": valid,
        "invalid_proofs": sum(1 for p in proofs if p.get("status") == "invalid"),
        "pending_proofs": sum(1 for p in proofs if p.get("status") == "submitted"),
        "success_rate": round(valid / total * 100, 2) if total > 0 else 0,
        "avg_gas": avg_gas,
        "total_batches": len(batches),
        "protocol": "groth16",
        "curve": "bn128",
        "circuit": "BalanceVerifier"
    }
