// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Verifier.sol";

contract AuditManager {
    Groth16Verifier public verifier;
    address public authorizedAuditor;

    constructor(address _verifierAddress) {
        verifier = Groth16Verifier(_verifierAddress);
        authorizedAuditor = msg.sender; 
    }

    function verifyAudit(
        uint[2] calldata pA,
        uint[2][2] calldata pB,
        uint[2] calldata pC,
        uint[5] calldata pubSignals
    ) public view returns (bool) {
        require(msg.sender == authorizedAuditor, "Unauthorized: Only the Auditor can submit proofs.");
        return verifier.verifyProof(pA, pB, pC, pubSignals);
    }
}