import { network } from "hardhat";
import fs from "fs";

async function main() {
  const { ethers } = await network.connect();
  const batchAddress = fs.readFileSync("deployed_batch_address.txt", "utf8").trim();
  const proof = JSON.parse(fs.readFileSync("proof.json", "utf8"));
  const pubSignals = JSON.parse(fs.readFileSync("public.json", "utf8"));

  const batchVerifier = await ethers.getContractAt("VATABatchVerifier", batchAddress);

  const pA = [proof.pi_a[0], proof.pi_a[1]];
  const pB = [
    [proof.pi_b[0][1], proof.pi_b[0][0]],
    [proof.pi_b[1][1], proof.pi_b[1][0]]
  ];
  const pC = [proof.pi_c[0], proof.pi_c[1]];

  const singleProof = { pA, pB, pC, pubSignals };
  const batch = Array(5).fill(singleProof);

  console.log("??  SUBMITTING BATCH OF", batch.length, "PROOFS...");

  // Use callStatic to get return value
  const results = await batchVerifier.verifyBatch.staticCall(batch);

  console.log("----------------------------------------------");
  let validCount = 0;
  for (const r of results) {
    const valid = r.valid;
    if (valid) validCount++;
    console.log(`Proof ${Number(r.index) + 1}: ${valid ? "? VALID" : "? INVALID"}`);
  }
  console.log("----------------------------------------------");
  console.log(`? BATCH COMPLETE: ${validCount}/${batch.length} proofs valid`);
  console.log("----------------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
