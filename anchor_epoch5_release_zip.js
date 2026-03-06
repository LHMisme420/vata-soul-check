#!/usr/bin/env node
/**
 * Anchor Epoch 5 release bundle ZIP hash (SHA-256) onchain.
 *
 * Usage (PowerShell):
 *   $env:RPC="https://ethereum-sepolia-rpc.publicnode.com"
 *   $env:PK="0xYOUR_PRIVATE_KEY"
 *   # optional:
 *   $env:ANCHOR_ADDR="0xYourAnchorContract"
 *   node .\anchor_epoch5_release_zip.js
 *
 * Requirements:
 *   npm i ethers
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

function die(msg) {
  console.error(msg);
  process.exit(1);
}

function exists(p) {
  try { fs.accessSync(p); return true; } catch { return false; }
}

function readText(p) {
  return fs.readFileSync(p, "utf8");
}

function sha256FileHex(filePath) {
  const buf = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function toBytes32FromHex(hexNo0x) {
  const h = hexNo0x.toLowerCase().replace(/^0x/, "");
  if (h.length !== 64) {
    die(`Expected 32-byte hex (64 chars). Got length=${h.length}`);
  }
  return "0x" + h;
}

function findFirstAddressInText(txt) {
  const m = txt.match(/0x[a-fA-F0-9]{40}/);
  return m ? m[0] : null;
}

/**
 * Try to discover an anchor/registry address from local repo files.
 * It searches for tokens like SIMPLE_REGISTRY / REG / ANCHOR / CONTRACT, then grabs an address.
 */
function discoverAnchorAddress() {
  const candidates = [
    "receipts_verify_onchain.txt",
    path.join("receipts", "receipts_verify_onchain.txt"),
    "verify_anchor.ps1",
    path.join("receipts", "sepolia_epoch5_receipt.json"),
    path.join("receipts", "epoch5_manifest.json"),
  ];

  // Also scan receipts folder for anything epoch5-ish
  if (exists("receipts")) {
    for (const f of fs.readdirSync("receipts")) {
      if (/epoch5/i.test(f) && /\.json$|\.txt$|\.md$/i.test(f)) {
        candidates.push(path.join("receipts", f));
      }
    }
  }

  const keywords = [
    "SIMPLE_REGISTRY",
    "REGISTRY",
    "REG:",
    "ANCHOR",
    "ANCHOR:",
    "CONTRACT",
    "ADDRESS",
  ];

  for (const p of candidates) {
    if (!exists(p)) continue;
    const txt = readText(p);

    // Prefer a line containing keywords
    for (const k of keywords) {
      const lines = txt.split(/\r?\n/).filter(l => l.includes(k));
      for (const line of lines) {
        const addr = findFirstAddressInText(line);
        if (addr) return addr;
      }
    }

    // fallback: first address anywhere
    const any = findFirstAddressInText(txt);
    if (any) return any;
  }

  return null;
}

/**
 * Search Foundry artifacts (./out/**.json) to load ABI for a contract.
 * Returns { abi, contractName, artifactPath } or null.
 */
function findAnyAbiArtifact() {
  const outDir = "out";
  if (!exists(outDir)) return null;

  // Walk directory recursively (shallow enough for Foundry out/)
  function walk(dir) {
    const res = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) res.push(...walk(p));
      else if (entry.isFile() && p.toLowerCase().endsWith(".json")) res.push(p);
    }
    return res;
  }

  const files = walk(outDir);

  // Prefer likely names if present
  const preferredNameHints = [
    "ManifestAnchor",
    "SimpleRegistry",
    "Registry",
    "Anchor",
    "Truth",
    "Verifier",
  ];

  const scored = files
    .map(fp => {
      const base = path.basename(fp);
      let score = 0;
      for (const h of preferredNameHints) {
        if (base.includes(h)) score += 10;
      }
      // prefer artifacts with ".sol/" path shape
      if (fp.includes(".sol")) score += 2;
      return { fp, score };
    })
    .sort((a, b) => b.score - a.score);

  for (const { fp } of scored) {
    try {
      const j = JSON.parse(readText(fp));
      if (j && Array.isArray(j.abi) && j.abi.length > 0) {
        return {
          abi: j.abi,
          contractName: j.contractName || path.basename(fp, ".json"),
          artifactPath: fp,
        };
      }
    } catch {
      // ignore
    }
  }

  return null;
}

async function main() {
  const RPC = process.env.RPC || process.env.SEPOLIA_RPC || process.env.RPC_URL;
  const PK = process.env.PK || process.env.PRIVATE_KEY;

  if (!RPC) die("Missing RPC env var. Set $env:RPC='https://…'");
  if (!PK) die("Missing PK env var. Set $env:PK='0x…'");

  const zipPath = path.join("evidence", "epoch5_release.zip");
  if (!exists(zipPath)) die(`Missing ${zipPath}. Create the zip first.`);

  const zipSha = sha256FileHex(zipPath);
  const zipBytes32 = toBytes32FromHex(zipSha);

  // Anchor address
  const envAddr = process.env.ANCHOR_ADDR;
  const autoAddr = discoverAnchorAddress();
  const ANCHOR_ADDR = envAddr || autoAddr;
  if (!ANCHOR_ADDR) {
    die(
      "Could not auto-detect anchor contract address.\n" +
      "Set it explicitly: $env:ANCHOR_ADDR='0x...'\n"
    );
  }

  // Load ethers
  let ethers;
  try {
    ethers = require("ethers");
  } catch (e) {
    die("Missing dependency 'ethers'. Run: npm i ethers");
  }

  const provider = new ethers.JsonRpcProvider(RPC);
  const wallet = new ethers.Wallet(PK, provider);

  console.log("=== Epoch 5 Release ZIP Anchor ===");
  console.log("ZIP:", zipPath);
  console.log("ZIP SHA256:", zipSha.toUpperCase());
  console.log("bytes32:", zipBytes32);
  console.log("From:", wallet.address);
  console.log("Anchor contract:", ANCHOR_ADDR);

  // ABI resolution: try Foundry out/ first
  let abiInfo = findAnyAbiArtifact();
  let abi = abiInfo ? abiInfo.abi : null;

  // If no ABI found, fall back to minimal ABIs with common method names
  const fallbackAbis = [
    ["function anchor(bytes32) external"],
    ["function set(bytes32) external"],
    ["function commit(bytes32) external"],
    ["function publish(bytes32) external"],
    ["function submit(bytes32) external"],
    ["function register(bytes32) external"],
    ["function add(bytes32) external"],
    ["function store(bytes32) external"],
  ];

  async function trySendWithAbi(methodAbiArr) {
    const c = new ethers.Contract(ANCHOR_ADDR, methodAbiArr, wallet);
    const fn = Object.keys(c.interface.functions)[0]; // only one
    const name = fn.split("(")[0];
    console.log("Trying method:", name);

    const tx = await c[name](zipBytes32);
    console.log("TX hash:", tx.hash);
    const rcpt = await tx.wait();
    console.log("Anchored in block:", rcpt.blockNumber);
    return { txHash: tx.hash, block: rcpt.blockNumber, method: name };
  }

  // First try with discovered ABI (if we have it)
  if (abi) {
    const contract = new ethers.Contract(ANCHOR_ADDR, abi, wallet);

    // Find a compatible function automatically
    const candidates = [
      "anchor",
      "set",
      "commit",
      "publish",
      "submit",
      "register",
      "add",
      "store",
    ];

    for (const name of candidates) {
      try {
        const frag = contract.interface.getFunction(name);
        // Ensure it takes 1 arg of type bytes32-ish
        if (!frag || frag.inputs.length !== 1) continue;

        // Send
        console.log("Using ABI artifact:", abiInfo.contractName, "(", abiInfo.artifactPath, ")");
        console.log("Calling:", name, "(bytes32)");
        const tx = await contract[name](zipBytes32);
        console.log("TX hash:", tx.hash);
        const rcpt = await tx.wait();
        console.log("Anchored in block:", rcpt.blockNumber);
        return;
      } catch {
        // keep trying
      }
    }
    console.log("ABI found but no matching 1-arg bytes32 method; falling back to common minimal ABIs…");
  }

  // Fallback ABIs
  for (const a of fallbackAbis) {
    try {
      await trySendWithAbi(a);
      return;
    } catch (e) {
      // try next
    }
  }

  die("Failed to anchor: no compatible function found, or tx reverted. Set correct ANCHOR_ADDR / ensure ABI exists in ./out.");
}

main().catch((e) => {
  console.error("FATAL:", e?.message || e);
  process.exit(1);
});