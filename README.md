---
title: VATA — Verifiable AI Truth Architecture
emoji: 🔐
colorFrom: gray
colorTo: gray
sdk: static
app_file: index.html
pinned: false
---

# VATA — Verifiable AI Truth Architecture

VATA is a reproducible zero-knowledge proof drop demonstrating verifiable computation for AI pipelines.

This repository contains:

- Arithmetic circuit (Circom)
- Groth16 proof
- Verification key
- Solidity verifier
- Deterministic SHA256 manifest
- On-chain timestamp anchor

---

## ?? Proof Pack (Score30)

?? Browse files:
https://huggingface.co/spaces/Lhmisme/vata-soul-check/tree/main/proofpack/score30

?? Manifest (SHA256 hashes):
https://huggingface.co/spaces/Lhmisme/vata-soul-check/blob/main/proofpack/score30/MANIFEST.txt

?? One-command verification:
https://huggingface.co/spaces/Lhmisme/vata-soul-check/blob/main/proofpack/score30/REPRO.ps1

---

## ? Verify Locally (Windows PowerShell)

powershell -ExecutionPolicy Bypass -File proofpack\score30\REPRO.ps1

Expected output:

snarkJS: OK!

---

## ? On-Chain Anchor (Sepolia)

Transaction:
0x7369b194ec8ed858b22437bbd824d6f8b2948f9ade5b11c13bd24fe0778a9fd5

Block:
10334791

Address:
0xF230c3221F83840d31A8c34f7d6dbB6Be2Af1069

ZIP SHA256:
6D7186760636DE5F0F306D089B7D21AF64EEECEACC2D049BF3B9BFFEDF0AB495

---

## Principle

Don't trust. Verify.
