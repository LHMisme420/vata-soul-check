pragma circom 2.0.0;

include "poseidon.circom";

template SemanticContradiction() {
    signal input emb_hash_a;
    signal input emb_hash_b;
    signal input distance_int;
    signal input threshold;

    signal output is_contradiction;
    signal output commitment;

    signal geq;
    geq <-- distance_int >= threshold ? 1 : 0;
    geq * (1 - geq) === 0;

    signal bound;
    bound <== geq * (distance_int - threshold);
    signal bound_bits[20];
    var bv = bound;
    for (var i = 0; i < 20; i++) {
        bound_bits[i] <-- (bv >> i) & 1;
        bound_bits[i] * (1 - bound_bits[i]) === 0;
        bv = bv - bound_bits[i] * (1 << i);
    }
    var bound_reconstructed = 0;
    for (var i = 0; i < 20; i++) {
        bound_reconstructed += bound_bits[i] * (1 << i);
    }
    bound === bound_reconstructed;

    is_contradiction <== geq;

    component cm = Poseidon(3);
    cm.inputs[0] <== emb_hash_a;
    cm.inputs[1] <== emb_hash_b;
    cm.inputs[2] <== distance_int;
    commitment <== cm.out;
}

component main {public [threshold]} = SemanticContradiction();
