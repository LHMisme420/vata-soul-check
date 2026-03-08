pragma circom 2.0.0;

include "poseidon.circom";

/*
 * VATA Non-Determinism Circuit
 * Leroy H. Malak / LHMisme420
 *
 * Proves a model is stochastic — responded differently
 * across N runs of the same prompt — without revealing
 * any response or the prompt itself.
 *
 * Private inputs:
 *   hash_0, hash_1, hash_2 : SHA256 of 3 runs (as field elements)
 *
 * Public inputs:
 *   session_id : Poseidon(hash_0, hash_1, hash_2) - audit session binder
 *
 * Public outputs:
 *   is_nondeterministic : 1 if any two hashes differ
 *   commitment : Poseidon(hash_0, hash_1, hash_2, is_nondeterministic)
 */

template IsNonZero() {
    signal input in;
    signal output out;
    signal inv;
    inv <-- in != 0 ? (1 / in) : 0;
    out <== in * inv;
    in * (1 - out) === 0;
}

template NonDeterminism() {
    signal input hash_0;
    signal input hash_1;
    signal input hash_2;
    signal input session_id;

    signal output is_nondeterministic;
    signal output commitment;

    // Check each pair for difference
    signal diff_01;
    signal diff_02;
    signal diff_12;

    diff_01 <== hash_0 - hash_1;
    diff_02 <== hash_0 - hash_2;
    diff_12 <== hash_1 - hash_2;

    component nz_01 = IsNonZero();
    component nz_02 = IsNonZero();
    component nz_12 = IsNonZero();

    nz_01.in <== diff_01;
    nz_02.in <== diff_02;
    nz_12.in <== diff_12;

    // any_diff = 1 if any pair differs
    signal any_01_02;
    any_01_02 <== nz_01.out + nz_02.out - nz_01.out * nz_02.out;
    signal any_diff;
    any_diff <== any_01_02 + nz_12.out - any_01_02 * nz_12.out;

    is_nondeterministic <== any_diff;

    // Verify session_id binds to these exact hashes
    component fp = Poseidon(3);
    fp.inputs[0] <== hash_0;
    fp.inputs[1] <== hash_1;
    fp.inputs[2] <== hash_2;
    fp.out === session_id;

    // Commitment
    component cm = Poseidon(4);
    cm.inputs[0] <== hash_0;
    cm.inputs[1] <== hash_1;
    cm.inputs[2] <== hash_2;
    cm.inputs[3] <== is_nondeterministic;
    commitment <== cm.out;
}

component main {public [session_id]} = NonDeterminism();