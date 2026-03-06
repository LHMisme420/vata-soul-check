from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from store.db import get_all_proofs, add_proof
from guardian import guardian_check
import hashlib, json, time

router = APIRouter()

class ProofSubmission(BaseModel):
    pi_a: List[str]
    pi_b: List[List[str]]
    pi_c: List[str]
    pub_signals: List[str]
    network: Optional[str] = "sepolia"
    verifier_address: Optional[str] = ""

@router.get("/")
def list_proofs():
    return {"proofs": get_all_proofs()}

@router.post("/submit")
def submit_proof(body: ProofSubmission):
    # Guardian PII check
    guard = guardian_check(body.pub_signals)
    if guard["blocked"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "GUARDIAN_BLOCKED",
                "message": "PII detected in public signals",
                "findings": guard["findings"]
            }
        )

    start = time.time()
    proof_json = json.dumps({
        "pi_a": body.pi_a,
        "pi_b": body.pi_b,
        "pi_c": body.pi_c,
        "pub_signals": body.pub_signals
    }, sort_keys=True)
    proof_hash = "0x" + hashlib.sha256(proof_json.encode()).hexdigest()
    elapsed = round((time.time() - start) * 1000, 2)

    record = add_proof({
        "hash": proof_hash,
        "pi_a": body.pi_a,
        "pi_b": body.pi_b,
        "pi_c": body.pi_c,
        "pub_signals": body.pub_signals,
        "network": body.network,
        "verifier_address": body.verifier_address,
        "status": "submitted",
        "proof_time_ms": elapsed,
        "gas_used": None,
        "tx_hash": None,
        "guardian": "PASS"
    })
    return {"success": True, "proof": record, "guardian": guard}

@router.get("/{proof_id}")
def get_proof(proof_id: int):
    proofs = get_all_proofs()
    match = next((p for p in proofs if p["id"] == proof_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Proof not found")
    return match
