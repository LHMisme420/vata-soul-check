pragma circom 2.0.0;

include "circomlib/circuits/sha256.circom";

template DoubleHash() {
    signal input in[512];
    signal output out[256];

    component h1 = Sha256(512);
    component h2 = Sha256(256);

    for (var i = 0; i < 512; i++) {
        h1.in[i] <== in[i];
    }

    for (var j = 0; j < 256; j++) {
        h2.in[j] <== h1.out[j];
        out[j] <== h2.out[j];
    }
}

component main = DoubleHash();