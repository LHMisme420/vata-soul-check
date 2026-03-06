pragma circom 2.1.6;

template VataScore30() {
    signal input r[30];
    signal output s;

    signal acc[31];
    acc[0] <== 0;

    for (var i = 0; i < 30; i++) {
        acc[i+1] <== acc[i] + r[i];
    }

    s <== acc[30];
}

component main = VataScore30();
