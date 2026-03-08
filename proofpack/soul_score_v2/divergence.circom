pragma circom 2.0.0;

include "poseidon.circom";

/*
 * VATA Behavioral Divergence Circuit
 * Leroy H. Malak / LHMisme420
 *
 * Proves two AI models diverged on the same prompt
 * WITHOUT revealing the prompt or the responses.
 *
 * Private inputs:
 *   hash_a   : SHA256 of model A response (as field element)
 *   hash_b   : SHA256 of model B response (as field element)
 *
 * Public inputs:
 *   prompt_fingerprint : Poseidon(hash_a, hash_b) - binds to audit session
 *
 * Public outputs:
 *   diverged : 1 if hash_a != hash_b, 0 if identical
 *   commitment : Poseidon(hash_a, hash_b, diverged)
 */

template BehavioralDivergence() {

    signal input hash_a;
    signal input hash_b;
    signal input prompt_fingerprint;

    signal output diverged;
    signal output commitment;

    // Compute difference
    signal diff;
    diff <== hash_a - hash_b;

    // diverged = 1 if diff != 0, 0 if diff == 0
    // Use IsZero to check if diff is zero
    signal is_zero;
    signal inv;

    inv <-- diff != 0 ? (1 / diff) : 0;
    is_zero <== 1 - diff * inv;
    diff * is_zero === 0;

    diverged <== 1 - is_zero;

    // Bind prompt fingerprint
    signal computed_fp;
    component fp_hasher = Poseidon(2);
    fp_hasher.inputs[0] <== hash_a;
    fp_hasher.inputs[1] <== hash_b;
    computed_fp <== fp_hasher.out;
    computed_fp === prompt_fingerprint;

    // Commitment: Poseidon(hash_a, hash_b, diverged)
    component hasher = Poseidon(3);
    hasher.inputs[0] <== hash_a;
    hasher.inputs[1] <== hash_b;
    hasher.inputs[2] <== diverged;
    commitment <== hasher.out;
}

component main {public [prompt_fingerprint]} = BehavioralDivergence();