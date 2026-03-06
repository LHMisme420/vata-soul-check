const hre = require("hardhat");
const fs = require("fs");

async function main() {
  await hre.run('compile');

  const [deployer] = await hre.ethers.getSigners();
  console.log("🚀 Deploying with account:", deployer.address);

  const Verifier = await hre.ethers.getContractFactory("Verifier");
  const verifier = await Verifier.deploy();

  await verifier.waitForDeployment();
  const address = await verifier.getAddress();

  console.log("----------------------------------------------");
  console.log("✅ VATA-VERIFIER SEATED (DEPLOYED)");
  console.log("Address: " + address);
  console.log("----------------------------------------------");
  
  fs.writeFileSync('deployed_address.txt', address);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});