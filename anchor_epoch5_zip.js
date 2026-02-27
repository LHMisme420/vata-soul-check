const fs = require("fs");
const crypto = require("crypto");
const { ethers } = require("ethers");

const RPC = process.env.RPC;
const PK  = process.env.PK;
const ANCHOR = process.env.ANCHOR_ADDR;

if (!RPC) throw new Error("Missing env RPC");
if (!PK) throw new Error("Missing env PK");
if (!ANCHOR) throw new Error("Missing env ANCHOR_ADDR");

const zipPath = "./evidence/epoch5_release.zip";
if (!fs.existsSync(zipPath)) throw new Error("Missing " + zipPath);

const zipBuf = fs.readFileSync(zipPath);
const sha = crypto.createHash("sha256").update(zipBuf).digest("hex");
const b32 = "0x" + sha.toLowerCase();

(async () => {
  const provider = new ethers.JsonRpcProvider(RPC);
  const wallet = new ethers.Wallet(PK, provider);

  const abi = ["function anchor(bytes32) external"];
  const c = new ethers.Contract(ANCHOR, abi, wallet);

  console.log("ZIP_SHA256:", sha.toUpperCase());
  console.log("BYTES32:", b32);
  console.log("FROM:", wallet.address);
  console.log("ANCHOR:", ANCHOR);

  const tx = await c.anchor(b32);
  console.log("TX hash:", tx.hash);

  const r = await tx.wait();
  console.log("Anchored in block:", r.blockNumber);
})();