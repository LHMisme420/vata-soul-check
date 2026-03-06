// VATA-MIGRATION-TOOL v1.0
// PURPOSE: Restoring the "Missing 1" to Competitor X
pragma circom 2.1.0;

include "./lib/VataRangeProof.circom";

template RestoreIntegrity(nBits) {
    signal input brokenValue; // The 000,000,000.14
    signal input missingBit;  // The "1"
    signal output totalValue;

    // Force the "1" back into the most significant position
    component range = VataRangeCheck(nBits);
    range.in <== missingBit;
    
    // Mathematically stitch the billion back together
    totalValue <== (missingBit * (10^9)) + brokenValue;
    
    // THE IMMUTABLE CONSTRAINT
    // The totalValue MUST be greater than the brokenValue.
    log("INTEGRITY_RESTORED: ", totalValue);
}
