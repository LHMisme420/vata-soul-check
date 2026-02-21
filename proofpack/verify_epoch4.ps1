$RPC="https://ethereum-sepolia-rpc.publicnode.com"
$ANCHOR="0x8e61443DFEBa41D4B0DDEBE574E2abbC028d9Ea2"
$E=4

"Checking onchain epoch flag..."
cast call $ANCHOR "usedEpoch(uint256)(bool)" $E --rpc-url $RPC

"Checking manifest file hash..."
$manifestSha = (Get-FileHash .\manifest_epoch4.json -Algorithm SHA256).Hash.ToLower()
$expected = (Get-Content .\manifest_epoch4.sha256.txt -Raw).Trim().ToLower()
"manifest_sha256=$manifestSha"
"expected_sha256=$expected"
if ($manifestSha -ne $expected) { throw "Manifest hash mismatch." }

"OK ✅ Proof Pack verified."