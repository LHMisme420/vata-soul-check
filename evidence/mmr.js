const crypto = require("crypto");

function sha256Hex(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

// Domain-separate leaf vs node so structure is unambiguous
function hashLeaf(hex32) {
  return sha256Hex(Buffer.from("00" + hex32, "hex"));
}
function hashNode(leftHex, rightHex) {
  return sha256Hex(Buffer.from("01" + leftHex + rightHex, "hex"));
}

class MMR {
  constructor() {
    this.peaks = []; // peaks by height
    this.size = 0;   // number of leaves
  }

  appendLeafHex(leafHex32) {
    // leafHex32: 64 hex chars (no 0x)
    let node = hashLeaf(leafHex32);
    let height = 0;

    while (this.peaks[height]) {
      node = hashNode(this.peaks[height], node);
      this.peaks[height] = null;
      height++;
    }
    this.peaks[height] = node;
    this.size++;
  }

  root() {
    // bag peaks left->right
    let r = null;
    for (const p of this.peaks) {
      if (!p) continue;
      r = r ? hashNode(p, r) : p;
    }
    return r || sha256Hex(Buffer.from("")); // empty root defined
  }

  toJSON() {
    return { size: this.size, peaks: this.peaks };
  }
}

module.exports = { MMR, sha256Hex };
