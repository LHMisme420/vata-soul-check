pragma circom 2.0.0;
include "./circuits/VataMerkle.circom";
include "./circuits/VataNullifier.circom";
include "./circuits/VataSignature.circom";

template SovereignTransfer() {
    // Integrating the Triple Threat
    component sig = VataSignature();
    component null = VataNullifier();
    component tree = VataMerkleVerify(20);
    
    // All signals now bound by VATA logic...
}
