import json
import os
from datetime import datetime

STORE_PATH = os.path.join(os.path.dirname(__file__), "data.json")

def _load():
    if not os.path.exists(STORE_PATH):
        return {"proofs": [], "batches": []}
    with open(STORE_PATH) as f:
        return json.load(f)

def _save(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_all_proofs():
    return _load()["proofs"]

def add_proof(proof: dict):
    data = _load()
    proof["id"] = len(data["proofs"]) + 1
    proof["timestamp"] = datetime.utcnow().isoformat()
    data["proofs"].append(proof)
    _save(data)
    return proof

def get_all_batches():
    return _load()["batches"]

def add_batch(batch: dict):
    data = _load()
    batch["id"] = len(data["batches"]) + 1
    batch["timestamp"] = datetime.utcnow().isoformat()
    data["batches"].append(batch)
    _save(data)
    return batch
