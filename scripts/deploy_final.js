import { network } from "hardhat";
import fs from "fs";

async function main() {
  const { ethers } = await network.connect();
  console.log("???  SEATING THE JUDGE...");
  const Verifier = await ethers.getContractFactory("Groth16Verifier");
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();
  const address = await verifier.getAddress();
  console.log("----------------------------------------------");
  console.log("? VATA-VERIFIER SEATED (DEPLOYED)");
  console.log("Address: " + address);
  console.log("----------------------------------------------");
  fs.writeFileSync("deployed_address.txt", address);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
