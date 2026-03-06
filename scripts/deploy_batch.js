import { network } from "hardhat";
import fs from "fs";

async function main() {
  const { ethers } = await network.connect();

  console.log("???  DEPLOYING MOCK VERIFIER + BATCH VERIFIER...");

  const Mock = await ethers.getContractFactory("MockVerifier");
  const mock = await Mock.deploy();
  await mock.waitForDeployment();
  const mockAddress = await mock.getAddress();
  console.log("MockVerifier:", mockAddress);

  const BatchVerifier = await ethers.getContractFactory("VATABatchVerifier");
  const batch = await BatchVerifier.deploy(mockAddress);
  await batch.waitForDeployment();
  const batchAddress = await batch.getAddress();

  console.log("----------------------------------------------");
  console.log("? VATA BATCH VERIFIER DEPLOYED");
  console.log("Address:", batchAddress);
  console.log("----------------------------------------------");

  fs.writeFileSync("deployed_batch_address.txt", batchAddress);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
