# ================================
# ZK Groth16 Demo (Windows Native)
# ================================
$ErrorActionPreference = "Stop"

function Say($m) { Write-Host $m -ForegroundColor Cyan }
function Die($m) { Write-Host "[FATAL] $m" -ForegroundColor Red; exit 1 }
function MustExist($p) { if (-not (Test-Path $p)) { Die "Missing: $p" } }

Say "[INFO] Starting Groth16 demo..."

# ----------------
# Workspace
# ----------------
$demo  = Join-Path $env:USERPROFILE "zk-demo"
$build = Join-Path $demo "build"

New-Item -ItemType Directory -Force -Path $build | Out-Null
Say "[INFO] demo  = $demo"
Say "[INFO] build = $build"

# ----------------
# Locate circom.exe automatically
# ----------------
Say "[STEP] Locating circom.exe ..."

$circomExe = Get-ChildItem -Path $env:USERPROFILE -Recurse -Filter "circom.exe" -ErrorAction SilentlyContinue |
             Select-Object -First 1 -ExpandProperty FullName

if (-not $circomExe) {
    Die "circom.exe not found anywhere under $env:USERPROFILE.
Build it with:
  cd C:\Users\lhmsi\circom\circom
  cargo build --release"
}

Say "[OK] circom = $circomExe"

# ----------------
# Ensure snarkjs
# ----------------
if (-not (Get-Command snarkjs -ErrorAction SilentlyContinue)) {
    Say "[INFO] Installing snarkjs..."
    npm install -g snarkjs
}

snarkjs --version | Out-Host

# ----------------
# Clean build dir
# ----------------
Say "[STEP] Cleaning build directory..."
Get-ChildItem $build -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# ----------------
# Write circuit
# ----------------
$circomFile = Join-Path $demo "square.circom"

@"
pragma circom 2.1.6;

template Square() {
    signal input x;
    signal input y;
    signal xx;

    xx <== x * x;
    xx === y;
}

component main { public [y] } = Square();
"@ | Set-Content -Encoding UTF8 -Path $circomFile

Say "[OK] Wrote circuit: $circomFile"

# ----------------
# Compile circuit
# ----------------
Say "[STEP] Compiling circuit..."
& $circomExe $circomFile --r1cs --wasm --sym -o $build

$r1cs    = Join-Path $build "square.r1cs"
$wasmDir = Join-Path $build "square_js"
$wasm    = Join-Path $wasmDir "square.wasm"
$witGen  = Join-Path $wasmDir "generate_witness.js"

MustExist $r1cs
MustExist $wasm
MustExist $witGen
Say "[OK] circom compilation successful"

# ----------------
# Powers of Tau
# ----------------
$ptau0 = Join-Path $build "pot12_0000.ptau"
$ptauF = Join-Path $build "pot12_final.ptau"

Say "[STEP] powersoftau new..."
snarkjs powersoftau new bn128 12 $ptau0 -v
MustExist $ptau0

Write-Host ""
Write-Host ">>> TYPE ANY RANDOM TEXT AND PRESS ENTER <<<" -ForegroundColor Yellow
snarkjs powersoftau contribute $ptau0 $ptauF --name="init" -v
MustExist $ptauF
Say "[OK] ptau finalized"

# ----------------
# Groth16 setup
# ----------------
$zkey0 = Join-Path $build "square_0000.zkey"
$zkeyF = Join-Path $build "square_final.zkey"
$vk    = Join-Path $build "verification_key.json"

Say "[STEP] groth16 setup..."
snarkjs groth16 setup $r1cs $ptauF $zkey0
MustExist $zkey0

Write-Host ""
Write-Host ">>> TYPE ANY RANDOM TEXT AND PRESS ENTER <<<" -ForegroundColor Yellow
snarkjs zkey contribute $zkey0 $zkeyF --name="final" -v
MustExist $zkeyF

snarkjs zkey export verificationkey $zkeyF $vk
MustExist $vk
Say "[OK] verification key created"

# ----------------
# Witness + Prove
# ----------------
Say "[STEP] Generating witness + proof..."

$inputPath = Join-Path $demo "input.json"
'{"x":7,"y":49}' | Set-Content -Encoding UTF8 -Path $inputPath
MustExist $inputPath

$wtns = Join-Path $build "witness.wtns"
node $witGen $wasm $inputPath $wtns
MustExist $wtns

$proof  = Join-Path $build "proof.json"
$public = Join-Path $build "public.json"

snarkjs groth16 prove $zkeyF $wtns $proof $public
MustExist $proof
MustExist $public

# ----------------
# Verify
# ----------------
Say "[STEP] Verifying proof..."
$verifyOut = snarkjs groth16 verify $vk $public $proof
$verifyOut | Out-Host
if ($verifyOut -notmatch "OK") { Die "Verification FAILED" }

# ----------------
# Hashes
# ----------------
$shaProof  = (Get-FileHash $proof  -Algorithm SHA256).Hash
$shaPublic = (Get-FileHash $public -Algorithm SHA256).Hash
$shaVK     = (Get-FileHash $vk     -Algorithm SHA256).Hash

Write-Host ""
Write-Host "SHA256(proof.json)  = $shaProof"  -ForegroundColor Yellow
Write-Host "SHA256(public.json) = $shaPublic" -ForegroundColor Yellow
Write-Host "SHA256(vk.json)     = $shaVK"     -ForegroundColor Yellow

# ----------------
# FINAL VERDICT
# ----------------
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "✅✅✅  PROOF VALID (Groth16)  ✅✅✅" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "DEMO DIR: $demo" -ForegroundColor Green
