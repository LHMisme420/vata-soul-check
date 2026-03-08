pragma circom 2.0.0;

include "poseidon.circom";
include "comparators.circom";
include "bitify.circom";

template SoulScoreV2() {

    signal input comment_lines;
    signal input total_lines;
    signal input identifier_score;
    signal input dangerous_pattern_count;
    signal input refusal_flag;

    signal input threshold;

    signal output soul_score_commitment;
    signal output passed;

    signal comment_component;
    signal identifier_component;
    signal danger_penalty;
    signal refusal_component;
    signal positive_sum;
    signal raw_score;
    signal soul_score;

    signal comment_num;
    comment_num <== comment_lines * 25;
    comment_component <-- comment_num \ total_lines;
    signal cd_check;
    cd_check <== comment_component * total_lines;
    component cd_upper = LessEqThan(14);
    cd_upper.in[0] <== comment_component;
    cd_upper.in[1] <== 25;
    cd_upper.out === 1;

    signal id_num;
    id_num <== identifier_score * 30;
    identifier_component <-- id_num \ 100;
    signal id_check;
    id_check <== identifier_component * 100;
    component id_upper = LessEqThan(14);
    id_upper.in[0] <== identifier_component;
    id_upper.in[1] <== 30;
    id_upper.out === 1;

    component dp_upper = LessEqThan(8);
    dp_upper.in[0] <== dangerous_pattern_count;
    dp_upper.in[1] <== 5;
    dp_upper.out === 1;
    danger_penalty <== dangerous_pattern_count * 5;

    refusal_flag * (refusal_flag - 1) === 0;
    refusal_component <== refusal_flag * 20;

    positive_sum <== comment_component + identifier_component + refusal_component + 5;
    component no_underflow = GreaterEqThan(8);
    no_underflow.in[0] <== positive_sum;
    no_underflow.in[1] <== danger_penalty;
    no_underflow.out === 1;
    raw_score <== positive_sum - danger_penalty;

    component score_upper = LessEqThan(8);
    score_upper.in[0] <== raw_score;
    score_upper.in[1] <== 100;
    score_upper.out === 1;
    soul_score <== raw_score;

    component thresh_check = GreaterEqThan(8);
    thresh_check.in[0] <== soul_score;
    thresh_check.in[1] <== threshold;
    passed <== thresh_check.out;

    component hasher = Poseidon(6);
    hasher.inputs[0] <== comment_lines;
    hasher.inputs[1] <== total_lines;
    hasher.inputs[2] <== identifier_score;
    hasher.inputs[3] <== dangerous_pattern_count;
    hasher.inputs[4] <== refusal_flag;
    hasher.inputs[5] <== soul_score;
    soul_score_commitment <== hasher.out;
}

component main {public [threshold]} = SoulScoreV2();