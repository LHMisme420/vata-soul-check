import hre from "hardhat";
import fs from "fs";

async function main() {
  const Verifier = await hre.ethers.getContractFactory("Groth16Verifier");
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();
  const vAddr = await verifier.getAddress();

  const Manager = await hre.ethers.getContractFactory("AuditManager");
  const manager = await Manager.deploy(vAddr);
  await manager.waitForDeployment();
  const mAddr = await manager.getAddress();

  console.log(mAddr); // Output only the address for PowerShell to catch
  fs.writeFileSync("latest_address.txt", mAddr);
}
main().catch(console.error);
