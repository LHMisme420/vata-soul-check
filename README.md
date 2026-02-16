## Verify (epoch2 v2)

Tx (mainnet): 0x0af11aa299ab9ae3e527d73ce252c78a5044fcecc3e881c8680663915a7ff6c0  
Manifest SHA-256: 0x9e517e034425eaab3a9dceb8fb95e30537529ede6c41d1081e6a779138506379

```powershell
$RPC="https://ethereum-rpc.publicnode.com"
$TX="0x0af11aa299ab9ae3e527d73ce252c78a5044fcecc3e881c8680663915a7ff6c0"
.\bundles\epoch2\verify_anchor.ps1 -Manifest .\bundles\epoch2\evidence_manifest.json -Tx $TX -Rpc $RPC


Then:
```powershell
git add README.md
git commit -m "Document epoch2 v2 verification"
git push

git tag -a v0.1.4 -m "Publish epoch2 v2 verification artifacts"
git push origin v0.1.4
