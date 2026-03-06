import os
import json
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", 11155111))
INTERVAL = int(os.getenv("ANCHOR_INTERVAL_SECONDS", 30))
STORE_PATH = os.path.join(os.path.dirname(__file__), "store", "data.json")
RECEIPTS_PATH = os.path.join(os.path.dirname(__file__), "store", "receipts.json")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

def load_store():
    if not os.path.exists(STORE_PATH):
        return {"proofs": [], "batches": []}
    with open(STORE_PATH) as f:
        return json.load(f)

def save_store(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_receipts():
    if not os.path.exists(RECEIPTS_PATH):
        return []
    with open(RECEIPTS_PATH) as f:
        return json.load(f)

def save_receipts(receipts):
    with open(RECEIPTS_PATH, "w") as f:
        json.dump(receipts, f, indent=2)

def anchor_proof(proof: dict) -> dict:
    payload = json.dumps({
        "id": proof["id"],
        "hash": proof["hash"],
        "pub_signals": proof.get("pub_signals", []),
        "timestamp": proof.get("timestamp", ""),
        "network": proof.get("network", ""),
    }, sort_keys=True)

    anchor_hash = "0x" + hashlib.sha256(payload.encode()).hexdigest()
    data_hex = w3.to_hex(text=anchor_hash)

    nonce = w3.eth.get_transaction_count(account.address)
    gas_estimate = w3.eth.estimate_gas({
        "from": account.address,
        "to": account.address,
        "value": 0,
        "data": data_hex,
    })

    tx = {
        "nonce": nonce,
        "to": account.address,
        "value": 0,
        "gas": gas_estimate + 10000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID,
        "data": data_hex,
    }

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "proof_id": proof["id"],
        "proof_hash": proof["hash"],
        "anchor_hash": anchor_hash,
        "tx_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "gas_used": receipt.gasUsed,
        "status": "anchored" if receipt.status == 1 else "failed",
        "anchored_at": datetime.utcnow().isoformat(),
        "network": "sepolia",
        "etherscan": f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}"
    }

def run():
    print(f"[VATA ANCHOR] Starting pipeline - wallet: {account.address}")
    print(f"[VATA ANCHOR] Connected to Sepolia: {w3.is_connected()}")
    print(f"[VATA ANCHOR] Polling every {INTERVAL}s for unanchored proofs...")

    while True:
        try:
            data = load_store()
            receipts = load_receipts()
            anchored_ids = {r["proof_id"] for r in receipts}

            pending = [
                p for p in data["proofs"]
                if p.get("status") == "submitted" and p["id"] not in anchored_ids
            ]

            if pending:
                print(f"[VATA ANCHOR] Found {len(pending)} unanchored proof(s)")
                for proof in pending:
                    try:
                        print(f"[VATA ANCHOR] Anchoring proof #{proof['id']} - {proof['hash'][:20]}...")
                        receipt = anchor_proof(proof)
                        receipts.append(receipt)
                        save_receipts(receipts)

                        for p in data["proofs"]:
                            if p["id"] == proof["id"]:
                                p["status"] = "anchored"
                                p["tx_hash"] = receipt["tx_hash"]
                                p["gas_used"] = receipt["gas_used"]
                        save_store(data)

                        print(f"[VATA ANCHOR] Anchored #{proof['id']} - TX: {receipt['tx_hash']}")
                        print(f"[VATA ANCHOR] Etherscan: {receipt['etherscan']}")
                    except Exception as e:
                        print(f"[VATA ANCHOR] ERROR anchoring #{proof['id']}: {e}")
            else:
                print(f"[VATA ANCHOR] No pending proofs - {datetime.utcnow().isoformat()}")

        except Exception as e:
            print(f"[VATA ANCHOR] Pipeline error: {e}")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    run()
