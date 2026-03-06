pragma circom 2.1.8;

template BalanceVerifier() {
    signal input balance;
    signal output balance_squared;
    balance_squared <== balance * balance;
}

component main {public [balance]} = BalanceVerifier();
