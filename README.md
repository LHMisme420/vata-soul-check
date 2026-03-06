# VATA — Verification of Authentic Thought Architecture

> Forensic-grade ZK proof infrastructure. Every claim, anchored on-chain. No promises. Receipts.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)
[![Chain: Ethereum](https://img.shields.io/badge/Chain-Ethereum-blue.svg)](https://ethereum.org)
[![Protocol: Groth16](https://img.shields.io/badge/Protocol-Groth16-cyan.svg)](https://eprint.iacr.org/2016/260)
[![Network: Sepolia](https://img.shields.io/badge/Network-Sepolia-orange.svg)](https://sepolia.etherscan.io)

---

## What is VATA?

VATA is a sovereign ZK proof registry. It generates cryptographic proofs of computational claims, anchors them immutably on Ethereum, and produces tamper-proof forensic receipts — independently verifiable by anyone, anywhere, forever.

Built under the **RU∞X (Recursive Sovereignty)** framework by [@lhmisme420](https://github.com/lhmisme420).

No trust required. The chain is the witness.

---

## Deployed Contracts

| Contract | Network | Address |
|---|---|---|
| Groth16Verifier | Sepolia | `0x5FbDB2315678afecb367f032d93F642f64180aa3` |
| VATABatchVerifier | Sepolia | `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512` |

---

## Architecture
```
Proof Input
    |
    v
ZK Circuit (circom/snarkjs)
    |
    v
Groth16 Proof + Public Signals
    |
    v
VATA REST API (FastAPI)
    |
    v
SHA256 Anchor Hash
    |
    v
Ethereum (Sepolia/Mainnet) --- Etherscan Receipt
    |
    v
Forensic Receipt (JSON) --- Tamper-Proof, Forever
```

---

## Stack

- **ZK Protocol**: Groth16 / BN128
- **Circuits**: circom + snarkjs
- **Contracts**: Solidity + Hardhat 3
- **API**: FastAPI (Python 3.14)
- **Anchor**: Web3.py + Ethereum
- **SDK**: PowerShell
- **Dashboard**: HTML5 + Vanilla JS

---

## Quick Start

### 1. Clone
```bash
git clone https://github.com/lhmisme420/vata.git
cd vata
```

### 2. Install dependencies
```bash
npm install
pip install fastapi uvicorn web3 python-dotenv --break-system-packages
```

### 3. Configure environment
```bash
cp api/.env.example api/.env
# Fill in SEPOLIA_RPC_URL and PRIVATE_KEY
```

### 4. Start the API
```powershell
cd api
uvicorn main:app --reload --port 8000
```

### 5. Start the anchor pipeline
```powershell
# New terminal
cd api
python anchor.py
```

### 6. Load the SDK
```powershell
. .\sdk\VATA.ps1
VATA-Status
VATA-Metrics
```

---

## SDK Commands
```powershell
VATA-Status                  # System health
VATA-Metrics                 # Proof registry stats
VATA-ListProofs              # All proofs + status
VATA-GetProof -Id 1          # Full forensic receipt by ID
VATA-SubmitProof             # Submit a single proof
VATA-SubmitBatch             # Submit up to 100 proofs
VATA-Help                    # All commands
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | System status |
| GET | `/metrics/` | Registry metrics |
| GET | `/proofs/` | List all proofs |
| POST | `/proofs/submit` | Submit a proof |
| GET | `/proofs/{id}` | Get proof by ID |
| GET | `/batches/` | List all batches |
| POST | `/batches/submit` | Submit a batch |

Interactive docs: `http://localhost:8000/docs`

---

## Forensic Receipt Example
```json
{
  "proof_id": 1,
  "proof_hash": "0x109153b3dbac58c697710f7db77e4df07e741ef6584bad268fe4dc433cda4d5f",
  "anchor_hash": "0x2a7f...",
  "tx_hash": "b8cef7a71c0558c1438757ea62ab4874a3b3199b0dd6cb9c2c2822385f559949",
  "block_number": 7842103,
  "gas_used": 23640,
  "status": "anchored",
  "anchored_at": "2026-03-06T10:13:31.088865",
  "network": "sepolia",
  "etherscan": "https://sepolia.etherscan.io/tx/b8cef7a71c0558c1..."
}
```

---

## RU∞X Sovereign Architecture

VATA is one component of the broader **RU∞X** ecosystem — a framework for building sovereign, forensically-verifiable systems that operate without institutional permission.

> Receipts over promises. Evidence over assertion. Sovereignty over dependence.

---

## License

GPL-3.0 — Open infrastructure for sovereign builders.

---

*Built by [@lhmisme420](https://github.com/lhmisme420) — independent technologist, sovereignty coach, forensic AI researcher.*
