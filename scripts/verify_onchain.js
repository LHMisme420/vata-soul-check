import { network } from "hardhat";
import fs from "fs";

async function main() {
  const { ethers } = await network.connect();
  const verifierAddress = fs.readFileSync("deployed_address.txt", "utf8").trim();
  const verifier = await ethers.getContractAt("Groth16Verifier", verifierAddress);

  const pA = ["0x27b4e917fc11ca45a1cc63e326dd99b42a8e2b313b5c069a032777ae024e7f7f", "0x22d523d35c1baccc656ab3b7d8e44a0360801467a2933173e2c5cfc0c8e19f91"];
  const pB = [["0x1b8c07703eb1391d114d732557af09eead9a85229c2e9fe06d05d20ed291bd4b", "0x11b57ec068f4558bf971fc1c0ea16dfd498145315da47d8796e9fece24d71a3f"],["0x10e15250290119c67fa19db9608ce62ab0a4834e434c25ec7f6454e1f91a3101", "0x012ffe58ae51112f931a14bab1634139bea0262078b46d3619e6087be6665acc"]];
  const pC = ["0x254ab392865fb40ec5d88e83d82742024986159e74d2aa6f502b94427fe38980", "0x2b8536f5b3f92e3b23d18124e61016c27ceff18b006fda5f9f9bf15975b0c50b"];
  const pubSignals = ["0x0000000000000000000000000000000000000000000000000de0b6b3a7640000","0x000000000000000000000000000000000000000000000000000000003b9aca00"];

  console.log("??  Submitting ZK-Proof to the Judge at:", verifierAddress);

  const iface = verifier.interface;
  const calldata = iface.encodeFunctionData("verifyProof", [pA, pB, pC, pubSignals]);
  const [signer] = await ethers.getSigners();

  // Try with explicit high gas limit
  const result = await signer.call({
    to: verifierAddress,
    data: calldata,
    gasLimit: 10000000n
  });
  console.log("Raw result:", result);
  console.log("Decoded:", result === "0x0000000000000000000000000000000000000000000000000000000000000001" ? "? VALID" : result === "0x0000000000000000000000000000000000000000000000000000000000000000" ? "? INVALID" : "?? UNEXPECTED");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
