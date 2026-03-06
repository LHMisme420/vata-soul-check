pragma circom 2.0.0;
include "../node_modules/circomlib/circuits/eddsaposeidon.circom";

// VATA-STD-03: THE IDENTITY SHIELD
// Verifies EdDSA signatures to prevent unauthorized state transitions.
template VataSignature() {
    signal input enabled;
    signal input ax; // Public Key X
    signal input ay; // Public Key Y
    signal input s;  // Signature S
    signal input r8x; // Signature R8 X
    signal input r8y; // Signature R8 Y
    signal input msg; // The Transaction Hash

    component verifier = EdDSAPoseidonVerifier();
    verifier.enabled <== enabled;
    verifier.ax <== ax;
    verifier.ay <== ay;
    verifier.s <== s;
    verifier.r8x <== r8x;
    verifier.r8y <== r8y;
    verifier.msg <== msg;

    // THE ABSOLUTE CONSTRAINT
    // If enabled is 1, the signature MUST be valid.
    // This prevents "Ghost Transactions" from being processed.
}
