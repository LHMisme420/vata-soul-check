$ErrorActionPreference="Stop"

if (!(Get-Command snarkjs -ErrorAction SilentlyContinue)) { throw "snarkjs not found in PATH" }
if (!(Get-Command node -ErrorAction SilentlyContinue))   { throw "node not found in PATH" }

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host "=== VERIFYING SNARK PROOF ==="
snarkjs groth16 verify .\vkey.json .\public.json .\proof.json

Write-Host "=== DONE ==="
