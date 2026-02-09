# AI Evidence Archive

This directory contains public, verifiable records of AI-generated artifacts
with cryptographic chain-of-custody.

Each entry includes:
- Deterministic manifest hash
- Merkle root
- On-chain anchor transaction
- Verified smart contract

All records are independently verifiable.

## Verification Steps

1. Recompute the manifest hash
2. Compare to the Merkle root
3. Verify the root exists in the on-chain event log
4. Confirm contract source is verified on Etherscan

No trust in the creator or AI vendor is required.
