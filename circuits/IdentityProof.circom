pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

template IdentityProof() {
    signal input secret;
    signal input salt;
    signal input commitment;
    signal output identity_hash;
    signal output verified;

    component hasher = Poseidon(2);
    hasher.inputs[0] <== secret;
    hasher.inputs[1] <== salt;
    identity_hash <== hasher.out;

    component eq = IsEqual();
    eq.in[0] <== identity_hash;
    eq.in[1] <== commitment;
    verified <== eq.out;
}

component main {public [commitment]} = IdentityProof();
