
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GalileoAnchor {
    event ProofAnchored(bytes32 indexed hash, uint256 timestamp, string label);
    
    mapping(bytes32 => uint256) public anchored;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function anchor(bytes32 hash, string calldata label) external {
        require(msg.sender == owner, 'Not owner');
        anchored[hash] = block.timestamp;
        emit ProofAnchored(hash, block.timestamp, label);
    }
    
    function isAnchored(bytes32 hash) external view returns (bool) {
        return anchored[hash] > 0;
    }
}
