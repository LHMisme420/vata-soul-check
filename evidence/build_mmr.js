const fs = require("fs");
const path = require("path");
const { MMR, sha256Hex } = require("./mmr");

const SKIP_DIRS = new Set([
  "node_modules", ".git", ".vercel", "forge-project", "circuits", "build",
  "vol_fast", "vol_20260215_055327"
]);

function isProbablyTextOrJson(p) {
  const ext = path.extname(p).toLowerCase();
  return [".json",".txt",".csv",".log",".ps1",".sol",".circom",".wtns",".zkey",".r1cs",".sym",".js",".ts",".md"].includes(ext);
}

function listFilesRecursive(rootDir) {
  const out = [];
  const stack = [rootDir];

  while (stack.length) {
    const cur = stack.pop();
    const st = fs.statSync(cur);
    if (st.isDirectory()) {
      const base = path.basename(cur);
      if (SKIP_DIRS.has(base)) continue;
      for (const name of fs.readdirSync(cur)) {
        stack.push(path.join(cur, name));
      }
    } else if (st.isFile()) {
      out.push(cur);
    }
  }
  return out;
}

function loadFileListFromJson(p) {
  const txt = fs.readFileSync(p, "utf8");
  const j = JSON.parse(txt);

  // Accept common shapes:
  // - ["a.txt","b.txt"]
  // - { "files": ["a.txt", ...] }
  // - { "items": [{"path":"a.txt"}, ...] }
  let files = [];

  if (Array.isArray(j)) files = j;
  else if (Array.isArray(j.files)) files = j.files;
  else if (Array.isArray(j.items)) {
    files = j.items.map(x => (typeof x === "string" ? x : x.path || x.file || x.name)).filter(Boolean);
  }

  // Normalize paths relative to CWD
  files = files.map(f => path.resolve(process.cwd(), f));
  return files;
}

function sha256FileHex32(p) {
  const buf = fs.readFileSync(p);
  return sha256Hex(buf); // 64 hex chars
}

function main() {
  const cwd = process.cwd();
  let files = [];

  const merkleFilesPath = path.join(cwd, "merkle_files.json");
  if (fs.existsSync(merkleFilesPath)) {
    try {
      files = loadFileListFromJson(merkleFilesPath);
      console.log(`Using file list from merkle_files.json (${files.length} entries)`);
    } catch (e) {
      console.log("merkle_files.json exists but couldn't parse it; falling back to directory scan.");
      files = [];
    }
  }

  if (!files.length) {
    console.log("Scanning directory for files...");
    files = listFilesRecursive(cwd)
      .filter(p => isProbablyTextOrJson(p))
      .filter(p => path.basename(p) !== "mmr_state.json")
      .filter(p => path.basename(p) !== "mmr_leaves.json")
      .filter(p => path.basename(p) !== "mmr_root_hex.txt");
  }

  files = files.filter(p => fs.existsSync(p));
  files.sort((a,b) => a.localeCompare(b)); // deterministic ordering

  const leaves = [];
  const mmr = new MMR();

  for (const p of files) {
    const h = sha256FileHex32(p);   // 64 hex chars
    leaves.push({ path: path.relative(cwd, p), sha256: "0x" + h });
    mmr.appendLeafHex(h);
  }

  const rootHex = "0x" + mmr.root();
  fs.writeFileSync(path.join(cwd, "mmr_root_hex.txt"), rootHex + "\n", "utf8");
  fs.writeFileSync(path.join(cwd, "mmr_state.json"), JSON.stringify({ root: rootHex, ...mmr.toJSON() }, null, 2), "utf8");
  fs.writeFileSync(path.join(cwd, "mmr_leaves.json"), JSON.stringify(leaves, null, 2), "utf8");

  console.log("MMR SIZE:", mmr.size);
  console.log("MMR ROOT:", rootHex);
  console.log("Wrote: mmr_root_hex.txt, mmr_state.json, mmr_leaves.json");
}

main();
