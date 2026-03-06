$ErrorActionPreference = "Stop"

$TX  = "0xaf798b0938302bb14271e57f21eb677005d337cffa9d8d4371cd57ed1fc8b5c0"
$RPCS = @(
  "https://ethereum-rpc.publicnode.com",
  "https://eth.llamarpc.com",
  "https://cloudflare-eth.com",
  "https://1rpc.io/eth",
  "https://eth.drpc.org"
)

function Get-InputFromCastTx {
  param([string]$TxHash)

  foreach ($rpc in $RPCS) {
    try {
      $raw = (cast tx $TxHash --rpc-url $rpc | Out-String)
      $m = [regex]::Match($raw, "^\s*input\s+0x([0-9a-fA-F]+)\s*$", "Multiline")
      if ($m.Success) {
        return @{ rpc=$rpc; hex=$m.Groups[1].Value }
      }
    } catch {}
  }
  throw "Could not read tx input via cast tx from any RPC."
}

# --- Local root ---
if (-not (Test-Path .\mmr_root_hex.txt)) { throw "Missing mmr_root_hex.txt. Run: node build_mmr.js" }
$LOCAL = (Get-Content .\mmr_root_hex.txt -Raw).Trim().ToLower()

# --- On-chain root from cast tx output ---
$got = Get-InputFromCastTx -TxHash $TX
$RPC_USED = $got.rpc
$hex = $got.hex

if ($hex.Length -lt 64) { throw "Input too short to contain 32-byte root (len=$($hex.Length))" }

$ONCHAIN = ("0x" + $hex.Substring($hex.Length - 64, 64)).ToLower()

"RPC_USED = $RPC_USED"
"LOCAL    = $LOCAL"
"ONCHAIN  = $ONCHAIN"
"TX       = $TX"

if ($LOCAL -eq $ONCHAIN) {
  "PASS ✅ MMR root matches mainnet anchor."
  cast receipt $TX --rpc-url $RPC_USED | Select-String "blockNumber|status|to|gasUsed"
  exit 0
} else {
  "FAIL ❌ Local MMR root does not match the on-chain anchored root."
  exit 1
}
