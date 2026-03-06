pragma circom 2.1.8;

include "node_modules/circomlib/circuits/bitify.circom";

// Verifies that 'balance' is a valid 64-bit integer (Range Proof)
// Essential for preventing overflow attacks in DeFi.
template BalanceVerifier() {
    signal input balance;
    component n2b = Num2Bits(64);
    n2b.in <== balance;
    
    // The bit-check is implicitly handled by Num2Bits' internal constraints
    // but a serious audit requires additional field-safety checks.
}

component main = BalanceVerifier();
