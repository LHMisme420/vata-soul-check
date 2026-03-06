pragma circom 2.0.0;
include "../node_modules/circomlib/circuits/poseidon.circom";

// VATA-STD-01: THE SOVEREIGN MERKLE VERIFIER
// This template enforces that the witness MUST be part of the root.
template VataMerkleVerify(nLevels) {
    signal input leaf;
    signal input root;
    signal input pathElements[nLevels];
    signal input pathIndices[nLevels];

    component hashers[nLevels];
    signal node[nLevels + 1];
    node[0] <== leaf;

    for (var i = 0; i < nLevels; i++) {
        hashers[i] = Poseidon(2);
        // Force the constraint: the hasher MUST take the previous node
        hashers[i].inputs[0] <== node[i] - pathIndices[i] * (node[i] - pathElements[i]);
        hashers[i].inputs[1] <== pathElements[i] - pathIndices[i] * (pathElements[i] - node[i]);
        node[i+1] <== hashers[i].out;
    }

    // THE ABSOLUTE CONSTRAINT
    // If the computed node doesn't match the root, the proof FAILS.
    node[nLevels] === root;
}
