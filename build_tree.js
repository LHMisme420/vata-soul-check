const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const circomlibjs = require("circomlibjs");

// BN254 scalar field prime
const FR =
  21888242871839275222246405745257275088548364400416034343698204186575808495617n;

function sha256Hex(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function hexToBigIntModFr(hex) {
  return BigInt("0x" + hex) % FR;
}

function buildMerkle(poseidon, leaves) {
  const depth = Math.ceil(Math.log2(Math.max(1, leaves.length)));
  const n = 1 << depth;

  const padded = leaves.slice();
  while (padded.length < n) padded.push(0n);

  const layers = [padded];
  for (let d = 0; d < depth; d++) {
    const next = [];
    for (let i = 0; i < layers[d].length; i += 2) {
      next.push(poseidon([layers[d][i], layers[d][i + 1]]));
    }
    layers.push(next);
  }
  return { depth, layers, root: layers[depth][0] };
}

function merkleProof(tree, index) {
  const { depth, layers } = tree;
  const pathIndices = [];
  const siblings = [];
  let idx = index;

  for (let d = 0; d < depth; d++) {
    const isRight = idx & 1;
    pathIndices.push(isRight);
    const sib = isRight ? idx - 1 : idx + 1;
    siblings.push(layers[d][sib]);
    idx = Math.floor(idx / 2);
  }
  return { pathIndices, siblings };
}

(async () => {
  const inputDir = process.argv[2] || ".";
  const targetFile = process.argv[3] || "evidence.txt";

  const poseidon = await circomlibjs.buildPoseidon();
  const F = poseidon.F;

  const files = fs
    .readdirSync(inputDir)
    .filter((f) => f.toLowerCase().endsWith(".txt"))
    .sort();

  if (files.length === 0) {
    console.error("No .txt files found.");
    process.exit(1);
  }

  const leaves = [];
  const meta = [];

  for (const f of files) {
    const buf = fs.readFileSync(path.join(inputDir, f));
    const h = sha256Hex(buf);
    const leaf = hexToBigIntModFr(h);
    leaves.push(leaf);
    meta.push({ file: f, sha256: h, leaf_dec: leaf.toString() });
  }

  const tree = buildMerkle((arr) => F.toObject(poseidon(arr)), leaves);

  const idx = files.indexOf(targetFile);
  if (idx < 0) {
    console.error("Target file not found:", targetFile);
    console.error("Found:", files);
    process.exit(1);
  }

  const proof = merkleProof(tree, idx);

  fs.writeFileSync("merkle_files.json", JSON.stringify(meta, null, 2));
  fs.writeFileSync(
    "merkle_root.json",
    JSON.stringify({ root: tree.root.toString(), depth: tree.depth }, null, 2)
  );
  fs.writeFileSync(
    "merkle_proof.json",
    JSON.stringify(
      {
        file: targetFile,
        index: idx,
        leaf: leaves[idx].toString(),
        root: tree.root.toString(),
        depth: tree.depth,
        siblings: proof.siblings.map((x) => x.toString()),
        pathIndices: proof.pathIndices
      },
      null,
      2
    )
  );

  console.log("Files:", files);
  console.log("Depth:", tree.depth);
  console.log("Root:", tree.root.toString());
})();