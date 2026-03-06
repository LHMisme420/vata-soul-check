$JS_DIR = "C:\Users\lhmsi\zk-saas\build\AuditTrail\AuditTrail_js"
$WASM_PATH = "$JS_DIR\AuditTrail.wasm"
$ZKEY_PATH = "C:\Users\lhmsi\zk-saas\build\AuditTrail\audit_final.zkey"

Write-Host "`n--- STEP 1: MODULE CHECK ---" -ForegroundColor Cyan
if (Test-Path "$JS_DIR\generate_witness.js") { 
    Rename-Item "$JS_DIR\generate_witness.js" "generate_witness.cjs" -Force 
    Rename-Item "$JS_DIR\witness_calculator.js" "witness_calculator.cjs" -Force
    (Get-Content "$JS_DIR\generate_witness.cjs") -replace "witness_calculator.js", "witness_calculator.cjs" | Set-Content "$JS_DIR\generate_witness.cjs"
    Write-Host "Patched .js to .cjs" -ForegroundColor Green
} else {
    Write-Host "Files already patched." -ForegroundColor Yellow
}

Write-Host "`n--- STEP 2: GENERATING WITNESS (N=100) ---" -ForegroundColor Cyan
node "$JS_DIR\generate_witness.cjs" $WASM_PATH input.json ./build/audit_witness_real.wtns

Write-Host "`n--- STEP 3: CREATING ZK-PROOF ---" -ForegroundColor Cyan
npx snarkjs groth16 prove $ZKEY_PATH ./build/audit_witness_real.wtns proof.json public.json

Write-Host "`n--- STEP 4: ON-CHAIN VERIFICATION ---" -ForegroundColor Cyan
npx hardhat run scripts/deploy_final.js --network localhost
npx hardhat run scripts/verify_onchain.js --network localhost
