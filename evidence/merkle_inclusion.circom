pragma circom 2.1.9;

include "poseidon.circom";

template MerkleInclusion(depth) {
    signal input leaf;
    signal input root;

    signal input siblings[depth];
    signal input pathIndices[depth];

    signal cur[depth + 1];
    signal diff[depth];
    signal t[depth];
    signal left[depth];
    signal right[depth];

    component h[depth];

    cur[0] <== leaf;

    for (var i = 0; i < depth; i++) {

        pathIndices[i] * (pathIndices[i] - 1) === 0;

        diff[i] <== siblings[i] - cur[i];
        t[i] <== pathIndices[i] * diff[i];

        left[i]  <== cur[i] + t[i];
        right[i] <== siblings[i] - t[i];

        h[i] = Poseidon(2);
        h[i].inputs[0] <== left[i];
        h[i].inputs[1] <== right[i];

        cur[i + 1] <== h[i].out;
    }

    cur[depth] === root;
}

component main = MerkleInclusion(2);