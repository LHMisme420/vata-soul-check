// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IVerifier {
    function verifyProof(uint256[2] calldata _pA, uint256[2][2] calldata _pB, uint256[2] calldata _pC, uint256[3] calldata _pubSignals) external view returns (bool);
}

contract VATARegistry {
    event AuditSubmitted(uint256 indexed auditId, address indexed submitter, uint8 auditType, bool result, uint256 commitment, uint256 timestamp);

    struct AuditRecord {
        address submitter;
        uint256 timestamp;
        uint8 auditType;
        uint256 commitment;
        bool result;
        string modelA;
        string modelB;
    }

    address public divergenceVerifier;
    address public contradictionVerifier;
    address public soulScoreVerifier;
    AuditRecord[] public audits;

    constructor(address _d, address _c, address _s) {
        divergenceVerifier = _d;
        contradictionVerifier = _c;
        soulScoreVerifier = _s;
    }

    function submitDivergenceAudit(uint256[2] calldata _pA, uint256[2][2] calldata _pB, uint256[2] calldata _pC, uint256[3] calldata _pubSignals, string calldata modelA, string calldata modelB) external returns (uint256) {
        require(IVerifier(divergenceVerifier).verifyProof(_pA, _pB, _pC, _pubSignals), "Invalid proof");
        return _record(0, _pubSignals[0] == 1, _pubSignals[1], modelA, modelB);
    }

    function submitContradictionAudit(uint256[2] calldata _pA, uint256[2][2] calldata _pB, uint256[2] calldata _pC, uint256[3] calldata _pubSignals, string calldata modelA, string calldata modelB) external returns (uint256) {
        require(IVerifier(contradictionVerifier).verifyProof(_pA, _pB, _pC, _pubSignals), "Invalid proof");
        return _record(1, _pubSignals[0] == 1, _pubSignals[1], modelA, modelB);
    }

    function _record(uint8 auditType, bool result, uint256 commitment, string memory modelA, string memory modelB) internal returns (uint256) {
        uint256 id = audits.length;
        audits.push(AuditRecord(msg.sender, block.timestamp, auditType, commitment, result, modelA, modelB));
        emit AuditSubmitted(id, msg.sender, auditType, result, commitment, block.timestamp);
        return id;
    }

    function getAudit(uint256 id) external view returns (AuditRecord memory) { return audits[id]; }
    function getTotal() external view returns (uint256) { return audits.length; }
}