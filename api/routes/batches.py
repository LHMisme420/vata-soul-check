from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from store.db import get_all_batches, add_batch, add_proof
import hashlib, json, time

router = APIRouter()

class BatchProof(BaseModel):
    pi_a: List[str]
    pi_b: List[List[str]]
    pi_c: List[str]
    pub_signals: List[str]

class BatchSubmission(BaseModel):
    proofs: List[BatchProof]
    network: Optional[str] = "sepolia"
    verifier_address: Optional[str] = ""

@router.get("/")
def list_batches():
    return {"batches": get_all_batches()}

@router.post("/submit")
def submit_batch(body: BatchSubmission):
    if len(body.proofs) == 0:
        return {"error": "Empty batch"}
    if len(body.proofs) > 100:
        return {"error": "Batch too large (max 100)"}

    start = time.time()
    submitted = []

    for p in body.proofs:
        proof_json = json.dumps({"pi_a": p.pi_a, "pi_b": p.pi_b, "pi_c": p.pi_c}, sort_keys=True)
        proof_hash = "0x" + hashlib.sha256(proof_json.encode()).hexdigest()
        record = add_proof({
            "hash": proof_hash,
            "pi_a": p.pi_a,
            "pi_b": p.pi_b,
            "pi_c": p.pi_c,
            "pub_signals": p.pub_signals,
            "network": body.network,
            "verifier_address": body.verifier_address,
            "status": "submitted",
            "proof_time_ms": None,
            "gas_used": None,
            "tx_hash": None,
        })
        submitted.append(record)

    elapsed = round((time.time() - start) * 1000, 2)
    batch = add_batch({
        "total": len(body.proofs),
        "network": body.network,
        "verifier_address": body.verifier_address,
        "proof_ids": [p["id"] for p in submitted],
        "elapsed_ms": elapsed,
        "status": "submitted"
    })

    return {"success": True, "batch": batch, "proofs": submitted}
