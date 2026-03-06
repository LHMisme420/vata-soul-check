import hre from "hardhat";
import fs from "fs";

async function main() {
  // Force a check on the HRE
  if (!hre.ethers) {
    throw new Error("❌ Plugin Error: Hardhat-Ethers is NOT loaded. Check your config!");
  }

  const { ethers } = hre;
  const [deployer] = await ethers.getSigners();
  
  console.log("🚀 Deploying with account:", deployer.address);

  const Verifier = await ethers.getContractFactory("Verifier");
  const verifier = await Verifier.deploy();

  await verifier.waitForDeployment();
  const address = await verifier.getAddress();

  console.log("----------------------------------------------");
  console.log("✅ VATA-VERIFIER SEATED (DEPLOYED)");
  console.log("Address:", address);
  console.log("----------------------------------------------");
  
  fs.writeFileSync('deployed_address.txt', address);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});