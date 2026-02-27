const { ethers } = require('ethers');

// ── Config ────────────────────────────────────────────────────────────────────
const RPC_URL        = process.env.ETH_RPC_URL;        // e.g. Alchemy or Infura mainnet
const PRIVATE_KEY    = process.env.ETH_PRIVATE_KEY;    // your deployer wallet
const CONTRACT_ADDR  = process.env.VATA_REGISTRY_ADDR; // your deployed VATARegistry

// ── ABI — minimal interface for anchoring ────────────────────────────────────
const ABI = [
    "function registerReport(bytes32 reportHash, string calldata metadata) external",
    "event ReportRegistered(address indexed registrant, bytes32 reportHash, string metadata, uint256 timestamp)"
];

// ── Payload ───────────────────────────────────────────────────────────────────
const MASTER_HASH = "0xE45142AD3ADE4A067CD6212EDD094D2C914A900F141DF9A00C102968F3CBDB4D";
const METADATA    = JSON.stringify({
    suite:    "VATA Sovereign Forensics Suite",
    version:  "1.0.0",
    phases:   ["P1","P2","P3","P4","P5","P6","TrackB","TrackF","L1B"],
    models:   ["gpt-4o","claude-sonnet-4-6","gemini-2.5-pro","grok-3-latest"],
    result:   "17/17 - 100% mitigation effectiveness",
    timestamp: new Date().toISOString(),
    github:   "https://github.com/LHMisme420/vata-soul-check"
});

async function anchor() {
    console.log("Connecting to Ethereum Mainnet...");
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const wallet   = new ethers.Wallet(PRIVATE_KEY, provider);
    const contract = new ethers.Contract(CONTRACT_ADDR, ABI, wallet);

    const network = await provider.getNetwork();
    const balance = await provider.getBalance(wallet.address);
    console.log("Network:  " + network.name);
    console.log("Wallet:   " + wallet.address);
    console.log("Balance:  " + ethers.formatEther(balance) + " ETH");
    console.log("Hash:     " + MASTER_HASH);
    console.log("Anchoring to VATARegistry...");

    const tx = await contract.registerReport(MASTER_HASH, METADATA);
    console.log("TX submitted: " + tx.hash);
    console.log("Waiting for confirmation...");

    const receipt = await tx.wait(1);
    console.log("CONFIRMED - Block: " + receipt.blockNumber);
    console.log("TX Hash:    " + receipt.hash);
    console.log("Gas used:   " + receipt.gasUsed.toString());

    // ── Write receipt ──────────────────────────────────────────────────────────
    const receipt_data = {
        master_hash:    MASTER_HASH,
        tx_hash:        receipt.hash,
        block_number:   receipt.blockNumber,
        block_timestamp: new Date().toISOString(),
        contract:       CONTRACT_ADDR,
        network:        "ethereum-mainnet",
        gas_used:       receipt.gasUsed.toString(),
        metadata:       JSON.parse(METADATA)
    };

    require('fs').writeFileSync(
        'C:/Users/lhmsi/repos/vata-soul-check/chain-anchor/ONCHAIN_RECEIPT.json',
        JSON.stringify(receipt_data, null, 2)
    );

    console.log("Receipt written to ONCHAIN_RECEIPT.json");
    console.log("VATA IS NOW IMMUTABLY ANCHORED TO ETHEREUM MAINNET.");
}

anchor().catch(console.error);
