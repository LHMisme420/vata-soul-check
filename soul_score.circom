pragma circom 2.1.5;

template SoulScoreThreshold(threshold) {
    signal input code_input[1024];  // padded code hash/input
    signal output valid;

    signal soul_score;
    soul_score <== 0;

    // Dummy hash-like accumulation (replace with real fingerprint logic)
    for (var i = 0; i < 1024; i++) {
        soul_score += code_input[i];
        soul_score *= 31;
    }

    soul_score = soul_score % 1000;

    valid <== (soul_score >= threshold);
}

component main {public [threshold]} = SoulScoreThreshold(420);  // threshold public