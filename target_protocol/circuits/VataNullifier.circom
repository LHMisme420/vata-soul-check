pragma circom 2.0.0;
include "../node_modules/circomlib/circuits/poseidon.circom";

// VATA-STD-02: THE DOUBLE-SPEND SHIELD
// Enforces a deterministic Nullifier based on the Secret Key and Note ID.
template VataNullifier() {
    signal input secretKey;
    signal input noteId;
    signal input nullifier;

    component hasher = Poseidon(2);
    hasher.inputs[0] <== secretKey;
    hasher.inputs[1] <== noteId;

    // THE ABSOLUTE CONSTRAINT
    // The nullifier MUST be the Poseidon hash of (secretKey, noteId).
    // If an attacker tries to use a random nullifier, this fails.
    nullifier === hasher.out;
}
