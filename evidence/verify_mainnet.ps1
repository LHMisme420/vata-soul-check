$RPC="https://ethereum-rpc.publicnode.com"
$TX=(Get-Content .\anchored_tx_mainnet.txt -Raw).Trim()
$EXPECTED=(Get-Content .\anchored_root_mainnet.txt -Raw).Trim().ToLower()

$raw = (cast tx $TX --rpc-url $RPC | Out-String)
$m = [regex]::Match($raw, "^\s*input\s+0x([0-9a-fA-F]+)\s*$", "Multiline")
if (-not $m.Success) { throw "Could not find input in tx output" }

$hex = $m.Groups[1].Value
$ONCHAIN = ("0x" + $hex.Substring($hex.Length-64,64)).ToLower()

"EXPECTED = $EXPECTED"
"ONCHAIN  = $ONCHAIN"
if ($EXPECTED -eq $ONCHAIN) { "PASS ✅ mainnet anchor verifies" } else { "FAIL ❌ mismatch" }
