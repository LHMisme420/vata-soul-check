pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/poseidon.circom";

template AuditTrail(N) {
    signal input events[N];
    signal input salt;
    signal input event_index;
    signal input event_value;

    signal output trail_root;
    signal output event_hash;
    signal output bound_hash;

    component hashers[N];
    signal chain[N];

    component first = Poseidon(2);
    first.inputs[0] <== events[0];
    first.inputs[1] <== salt;
    chain[0] <== first.out;

    for (var i = 1; i < N; i++) {
        hashers[i] = Poseidon(2);
        hashers[i].inputs[0] <== chain[i-1];
        hashers[i].inputs[1] <== events[i];
        chain[i] <== hashers[i].out;
    }

    trail_root <== chain[N-1];

    component ev_hasher = Poseidon(2);
    ev_hasher.inputs[0] <== event_value;
    ev_hasher.inputs[1] <== event_index;
    event_hash <== ev_hasher.out;

    component binder = Poseidon(3);
    binder.inputs[0] <== trail_root;
    binder.inputs[1] <== event_hash;
    binder.inputs[2] <== salt;
    bound_hash <== binder.out;
}

component main {public [event_index, event_value]} = AuditTrail(8);
