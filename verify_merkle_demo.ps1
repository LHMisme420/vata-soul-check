param(
  [string]$TargetFile = "evidence.txt"
)

$ErrorActionPreference = "Stop"

# Move to script folder
Set-Location $PSScriptRoot

if (-not (Test-Path ".\build_tree.js")) { throw "Missing build_tree.js" }
if (-not (Test-Path ".\merkle_inclusion.circom")) { throw "Missing merkle_inclusion.circom" }
if (-not (Test-Path ".\node_modules\circomlib\circuits\poseidon.circom")) { throw "Missing circomlib. Run: npm i circomlib circomlibjs" }

# Build tree + proof JSON
node .\build_tree.js . $TargetFile

# Read depth from merkle_root.json and patch circuit main depth automatically
$mr = Get-Content .\merkle_root.json -Raw | ConvertFrom-Json
$depth = [int]$mr.depth
Write-Host "Using depth=$depth" -ForegroundColor Green

$cir = Get-Content .\merkle_inclusion.circom -Raw
$cir = [regex]::Replace($cir, 'component\s+main\s*=\s*MerkleInclusion\(\d+\)\s*;', "component main = MerkleInclusion($depth);")
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $PSScriptRoot "merkle_inclusion.circom"), $cir, $utf8NoBom)

# Compile
circom .\merkle_inclusion.circom -l ".\node_modules\circomlib\circuits" --r1cs --wasm --sym -o .

# Build merkle_input.json from merkle_proof.json
$mp = Get-Content .\merkle_proof.json -Raw | ConvertFrom-Json

$input = [ordered]@{
  leaf        = "$($mp.leaf)"
  root        = "$($mp.root)"
  siblings    = @($mp.siblings | ForEach-Object { "$_" })
  pathIndices = @($mp.pathIndices)
}
($input | ConvertTo-Json -Depth 10) | Set-Content .\merkle_input.json -Encoding ASCII

# Witness
node .\merkle_inclusion_js\generate_witness.js .\merkle_inclusion_js\merkle_inclusion.wasm .\merkle_input.json .\merkle_witness.wtns

# Prove/verify (requires existing pot12_final.ptau OR create it)
if (-not (Test-Path ".\pot12_final.ptau")) {
  Write-Host "pot12_final.ptau not found; creating a small one (bn128, power=12)..." -ForegroundColor Yellow
  snarkjs powersoftau new bn128 12 pot12_0000.ptau -v
  snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau --name="demo" -v
  snarkjs powersoftau prepare phase2 pot12_0001.ptau pot12_final.ptau -v
}

snarkjs groth16 setup .\merkle_inclusion.r1cs .\pot12_final.ptau merkle_0000.zkey
snarkjs zkey contribute merkle_0000.zkey merkle_final.zkey --name="demo" -v
snarkjs zkey export verificationkey merkle_final.zkey merkle_vk.json
snarkjs groth16 prove merkle_final.zkey .\merkle_witness.wtns merkle_proof_zk.json merkle_public.json
snarkjs groth16 verify merkle_vk.json merkle_public.json merkle_proof_zk.json

Write-Host "`nOK: Merkle inclusion proof verified." -ForegroundColor Green
Write-Host "Root:" (Get-Content .\merkle_root.json -Raw)
