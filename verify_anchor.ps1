<# 
verify_anchor.ps1
Verifies that:
  - SHA256(receipt.json) == first bytes32 in tx.input
  - merkle_root_v2.txt   == second bytes32 in tx.input
for a given Ethereum mainnet transaction.

Exit codes:
  0 = proof valid
  1 = proof invalid / mismatch
  2 = usage / input error
  3 = tool / rpc error

Requires:
  - Foundry cast in PATH
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [string]$RpcUrl = "https://ethereum-rpc.publicnode.com",

  [Parameter(Mandatory=$false)]
  [string]$TxHash = "0xfce1402c3c4609910976b5be0dea00ccbe7a61d548fbc9b65ed748b45a02daa9",

  [Parameter(Mandatory=$false)]
  [string]$ReceiptPath = "C:\Users\lhmsi\Desktop\vata-run\epochs\epoch_20260215_185409\receipt.json",

  [Parameter(Mandatory=$false)]
  [string]$MerklePath  = "C:\Users\lhmsi\Desktop\vata-run\epochs\epoch_20260215_185409\merkle_root_v2.txt",

  [Parameter(Mandatory=$false)]
  [switch]$Quiet
)

function Fail([int]$Code, [string]$Msg) {
  if (-not $Quiet) { Write-Host $Msg }
  exit $Code
}

function Require-Cast {
  try {
    $null = (Get-Command cast -ErrorAction Stop)
  } catch {
    Fail 3 "ERROR: 'cast' not found in PATH. Install Foundry and ensure 'cast' is available."
  }
}

function Normalize-Bytes32([string]$s) {
  if (-not $s) { return $null }
  $t = $s.Trim().ToLower()
  if ($t.StartsWith("0x")) { $t = $t.Substring(2) }
  # Some files store without 0x; accept both. Must be 64 hex chars.
  if ($t -notmatch '^[0-9a-f]{64}$') { return $null }
  return "0x$t"
}

function Get-ExpectedReceiptSha([string]$path) {
  if (-not (Test-Path $path)) { Fail 2 "ERROR: receipt file not found: $path" }
  $h = (Get-FileHash $path -Algorithm SHA256).Hash.ToLower()
  return "0x$h"
}

function Get-ExpectedMerkleRoot([string]$path) {
  if (-not (Test-Path $path)) { Fail 2 "ERROR: merkle root file not found: $path" }
  $raw = (Get-Content $path -Raw).Trim()
  $norm = Normalize-Bytes32 $raw
  if (-not $norm) { Fail 2 "ERROR: merkle_root_v2.txt must be 32-byte hex (64 hex chars), with or without 0x. Got: '$raw'" }
  return $norm
}

function Get-OnchainInput([string]$rpc, [string]$tx) {
  if ($tx -notmatch '^0x[0-9a-fA-F]{64}$') { Fail 2 "ERROR: TxHash must be 0x + 64 hex chars. Got: $tx" }
  try {
    $inp = (cast tx --rpc-url $rpc $tx input) 2>&1
    $inp = ($inp | Out-String).Trim()
  } catch {
    Fail 3 "ERROR: failed to query tx input via cast."
  }
  if ($inp -notmatch '^0x[0-9a-fA-F]+$') {
    Fail 3 "ERROR: unexpected tx input response: $inp"
  }
  return $inp.ToLower()
}

function Decode-TwoBytes32([string]$inputHex) {
  # inputHex includes 0x. We expect exactly 64 bytes => 128 hex chars after 0x.
  $h = $inputHex.Substring(2)
  if ($h.Length -lt 128) { Fail 1 "ERROR: tx input too short to contain 2x bytes32. len(hex)=$($h.Length)" }
  # If longer, we still decode first 64 bytes (common if selector included). Here we intentionally decode first 64 bytes only.
  $a = "0x" + $h.Substring(0,64)
  $b = "0x" + $h.Substring(64,64)
  return @($a, $b)
}

# -----------------------------
# Main
# -----------------------------
Require-Cast

if (-not $Quiet) {
  Write-Host "RPC     : $RpcUrl"
  Write-Host "TX      : $TxHash"
  Write-Host "RECEIPT : $ReceiptPath"
  Write-Host "MERKLE  : $MerklePath"
  Write-Host ""
}

$expected_receipt = Get-ExpectedReceiptSha $ReceiptPath
$expected_merkle  = Get-ExpectedMerkleRoot $MerklePath

$input = Get-OnchainInput $RpcUrl $TxHash
$decoded = Decode-TwoBytes32 $input
$onchain_receipt = $decoded[0]
$onchain_merkle  = $decoded[1]

if (-not $Quiet) {
  Write-Host "expected_receipt=$expected_receipt"
  Write-Host "onchain_receipt =$onchain_receipt"
  Write-Host "expected_merkle =$expected_merkle"
  Write-Host "onchain_merkle  =$onchain_merkle"
  Write-Host ""
}

if ($expected_receipt -eq $onchain_receipt -and $expected_merkle -eq $onchain_merkle) {
  if (-not $Quiet) { Write-Host "✅ PROOF VALID — FILES MATCH MAINNET ANCHOR" }
  exit 0
} else {
  if (-not $Quiet) { Write-Host "❌ PROOF INVALID — MISMATCH" }
  exit 1
}
