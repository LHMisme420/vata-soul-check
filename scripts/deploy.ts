import { ethers } from "hardhat";

async function main() {
  const Verifier = await ethers.getContractFactory("Verifier");
  const verifier = await Verifier.deploy();

  await verifier.waitForDeployment();

  console.log("----------------------------------------------");
  console.log("VATA-VERIFIER DEPLOYED");
  console.log("Address:", await verifier.getAddress());
  console.log("Status: READY TO RECEIVE BILLION-DOLLAR PROOFS");
  console.log("----------------------------------------------");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});