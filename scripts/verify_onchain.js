import { ethers } from "ethers";
import fs from "fs";

async function main() {
    const proof = JSON.parse(fs.readFileSync("proof.json", "utf8"));
    const publicSignals = JSON.parse(fs.readFileSync("public.json", "utf8"));
    const verifierAddress = fs.readFileSync("latest_address.txt", "utf8").trim(); 

    const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
    const signer = await provider.getSigner();

    // MUST match the function in AuditManager.sol
    const abi = ["function verifyAudit(uint[2] pA, uint[2][2] pB, uint[2] pC, uint[5] _pubSignals) view returns (bool)"];
    const Manager = new ethers.Contract(verifierAddress, abi, signer);

    console.log(`\nÃ°Å¸â€ºÂ¡Ã¯Â¸Â Calling Secure Manager at ${verifierAddress}...`);
    
    try {
        const isValid = await Manager.verifyAudit(
            [proof.pi_a[0], proof.pi_a[1]],
            [[proof.pi_b[0][1], proof.pi_b[0][0]], [proof.pi_b[1][1], proof.pi_b[1][0]]],
            [proof.pi_c[0], proof.pi_c[1]],
            publicSignals
        );
        console.log(isValid ? "----------------------------------------------\nÃ¢Å“â€¦ AUTHORIZED & VALID\n----------------------------------------------" : "Ã¢ÂÅ’ INVALID");
    } catch (err) {
        console.error("Ã¢ÂÅ’ Contract Error:", err.message);
    }
}
main().catch(console.error);