
---

## Merkle Inclusion Circuit

This circuit proves that a leaf (SHA256(file) mod Fr) is included in a Poseidon Merkle tree.

- Public input: Merkle root
- Private inputs:
  - leaf
  - siblings[]
  - pathIndices[]

Hash function: Poseidon(2)
Selector logic implemented with quadratic-safe arithmetic.

To compile:

circom merkle_inclusion.circom -l node_modules/circomlib/circuits --r1cs --wasm --sym -o .

To generate witness:

node merkle_inclusion_js/generate_witness.js merkle_inclusion_js/merkle_inclusion.wasm merkle_input.json merkle_witness.wtns

To prove & verify:

snarkjs groth16 prove merkle_final.zkey merkle_witness.wtns proof.json public.json
snarkjs groth16 verify merkle_vk.json public.json proof.json

