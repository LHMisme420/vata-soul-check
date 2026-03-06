// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

interface IGroth16Verifier {
    function verifyProof(
        uint[2] calldata _pA,
        uint[2][2] calldata _pB,
        uint[2] calldata _pC,
        uint[2] calldata _pubSignals
    ) external view returns (bool);
}

contract VATABatchVerifier {
    IGroth16Verifier public verifier;
    address public owner;

    struct Proof {
        uint[2] pA;
        uint[2][2] pB;
        uint[2] pC;
        uint[2] pubSignals;
    }

    struct BatchResult {
        uint256 index;
        bool valid;
    }

    event BatchVerified(
        uint256 indexed batchId,
        uint256 total,
        uint256 validCount,
        uint256 invalidCount,
        uint256 timestamp
    );

    event ProofResult(
        uint256 indexed batchId,
        uint256 indexed index,
        bool valid
    );

    uint256 public batchCount;

    constructor(address _verifier) {
        verifier = IGroth16Verifier(_verifier);
        owner = msg.sender;
    }

    function verifyBatch(Proof[] calldata proofs) external returns (BatchResult[] memory results) {
        require(proofs.length > 0, "Empty batch");
        require(proofs.length <= 100, "Batch too large");

        uint256 batchId = ++batchCount;
        results = new BatchResult[](proofs.length);
        uint256 validCount = 0;

        for (uint256 i = 0; i < proofs.length; i++) {
            bool valid = verifier.verifyProof(
                proofs[i].pA,
                proofs[i].pB,
                proofs[i].pC,
                proofs[i].pubSignals
            );
            results[i] = BatchResult(i, valid);
            if (valid) validCount++;
            emit ProofResult(batchId, i, valid);
        }

        emit BatchVerified(batchId, proofs.length, validCount, proofs.length - validCount, block.timestamp);
        return results;
    }

    function verifyBatchView(Proof[] calldata proofs) external view returns (bool[] memory results) {
        require(proofs.length > 0, "Empty batch");
        require(proofs.length <= 100, "Batch too large");

        results = new bool[](proofs.length);
        for (uint256 i = 0; i < proofs.length; i++) {
            results[i] = verifier.verifyProof(
                proofs[i].pA,
                proofs[i].pB,
                proofs[i].pC,
                proofs[i].pubSignals
            );
        }
    }
}
