# verify_all.ps1
$ErrorActionPreference = "Stop"

$TX        = "0xa652865c1d2474890d402547384263f6e8eb04ca11fc504558d994a8a96888ca"
$PROOFHASH = "0x6a54c7d51f1c3140c23dd06e40985acde8a4c3ca53aabfebc20b314ab83d002b"
$PREFIX    = "0x56415441"
$RPC       = "https://rpc.ankr.com/eth_sepolia"

if (-not (Get-Command cast -ErrorAction SilentlyContinue)) { throw "cast.exe not found (install Foundry)" }
if (-not (Test-Path ".\forensic_proof.bin")) { throw "Missing forensic_proof.bin" }

# Local proof hash
$localSha = (Get-FileHash ".\forensic_proof.bin" -Algorithm SHA256).Hash.ToLower()

# Expected calldata
$expected = ($PREFIX + $PROOFHASH.Substring(2)).ToLower()

# Onchain input
$tx = cast tx $TX --rpc-url $RPC --json | ConvertFrom-Json
$onchain = ($tx.input).ToLower()

if ($onchain -ne $expected) {
  throw ("FAIL calldata mismatch
Expected: {0}
Onchain:   {1}" -f $expected, $onchain)
}

"OK: calldata matches VATA(prefix)+proofhash"
"OK: local forensic_proof.bin sha256 = $localSha"
"TX: $TX"
"RPC: $RPC"

# If evidence folder exists, hash-check it against manifest
if (Test-Path ".\evidence_manifest.json" -and (Test-Path ".\evidence")) {
  $m = Get-Content ".\evidence_manifest.json" -Raw | ConvertFrom-Json
  foreach ($it in $m.evidence_items) {
    $p = Join-Path ".\evidence" $it.name
    if (-not (Test-Path $p)) { throw "Missing evidence file: $($it.name)" }
    $h = (Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
    if ($h -ne ($it.sha256.ToLower())) {
      throw "FAIL evidence hash mismatch: $($it.name)"
    }
  }
  "OK: evidence items match manifest"
}
