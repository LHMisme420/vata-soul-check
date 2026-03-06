pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";

template PoseidonDouble() {
    signal input a;
    signal input b;
    signal output out;

    component p1 = Poseidon(2);
    p1.inputs[0] <== a;
    p1.inputs[1] <== b;

    component p2 = Poseidon(1);
    p2.inputs[0] <== p1.out;

    out <== p2.out;
}

component main = PoseidonDouble();