# VATA SDK - PowerShell
# Verification of Authentic Thought Architecture
# Usage: . .\VATA.ps1

$VATA_API = "http://127.0.0.1:8000"

function VATA-Status {
    $r = Invoke-RestMethod -Uri "$VATA_API/" -UseBasicParsing
    Write-Host "VATA SYSTEM: $($r.system) v$($r.version)" -ForegroundColor Cyan
    Write-Host "STATUS: $($r.status)" -ForegroundColor Green
    Write-Host "PROTOCOL: $($r.protocol) / $($r.curve)" -ForegroundColor Cyan
}

function VATA-Metrics {
    $r = Invoke-RestMethod -Uri "$VATA_API/metrics/" -UseBasicParsing
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "VATA METRICS" -ForegroundColor Cyan
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "Total Proofs  : $($r.total_proofs)"
    Write-Host "Valid         : $($r.valid_proofs)"
    Write-Host "Invalid       : $($r.invalid_proofs)"
    Write-Host "Pending       : $($r.pending_proofs)"
    Write-Host "Success Rate  : $($r.success_rate)%"
    Write-Host "Avg Gas       : $($r.avg_gas)"
    Write-Host "Total Batches : $($r.total_batches)"
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
}

function VATA-SubmitProof {
    param(
        [Parameter(Mandatory)][string[]]$PiA,
        [Parameter(Mandatory)][string[][]]$PiB,
        [Parameter(Mandatory)][string[]]$PiC,
        [Parameter(Mandatory)][string[]]$PubSignals,
        [string]$Network = "sepolia",
        [string]$VerifierAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
    )

    $body = @{
        pi_a = $PiA
        pi_b = $PiB
        pi_c = $PiC
        pub_signals = $PubSignals
        network = $Network
        verifier_address = $VerifierAddress
    } | ConvertTo-Json -Depth 5

    $r = Invoke-RestMethod -Uri "$VATA_API/proofs/submit" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "PROOF SUBMITTED" -ForegroundColor Green
    Write-Host "ID       : $($r.proof.id)"
    Write-Host "Hash     : $($r.proof.hash)"
    Write-Host "Network  : $($r.proof.network)"
    Write-Host "Status   : $($r.proof.status)"
    Write-Host "Time     : $($r.proof.proof_time_ms)ms"
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    return $r.proof
}

function VATA-GetProof {
    param([Parameter(Mandatory)][int]$Id)
    $r = Invoke-RestMethod -Uri "$VATA_API/proofs/$Id" -UseBasicParsing
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "PROOF #$($r.id)" -ForegroundColor Cyan
    Write-Host "Hash     : $($r.hash)"
    Write-Host "Status   : $($r.status)"
    Write-Host "Network  : $($r.network)"
    Write-Host "TX       : $($r.tx_hash)"
    Write-Host "Gas      : $($r.gas_used)"
    Write-Host "Time     : $($r.timestamp)"
    if ($r.tx_hash) {
        Write-Host "Etherscan: https://sepolia.etherscan.io/tx/$($r.tx_hash)" -ForegroundColor Blue
    }
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    return $r
}

function VATA-ListProofs {
    $r = Invoke-RestMethod -Uri "$VATA_API/proofs/" -UseBasicParsing
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "ALL PROOFS ($($r.proofs.Count) total)" -ForegroundColor Cyan
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    foreach ($p in $r.proofs) {
        $color = if ($p.status -eq "anchored") { "Green" } elseif ($p.status -eq "submitted") { "Yellow" } else { "Red" }
        Write-Host "#$($p.id) | $($p.hash.Substring(0,20))... | $($p.status) | $($p.network)" -ForegroundColor $color
    }
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
}

function VATA-SubmitBatch {
    param(
        [Parameter(Mandatory)][array]$Proofs,
        [string]$Network = "sepolia",
        [string]$VerifierAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
    )

    $body = @{
        proofs = $Proofs
        network = $Network
        verifier_address = $VerifierAddress
    } | ConvertTo-Json -Depth 10

    $r = Invoke-RestMethod -Uri "$VATA_API/batches/submit" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "BATCH SUBMITTED" -ForegroundColor Green
    Write-Host "Batch ID  : $($r.batch.id)"
    Write-Host "Total     : $($r.batch.total)"
    Write-Host "Network   : $($r.batch.network)"
    Write-Host "Elapsed   : $($r.batch.elapsed_ms)ms"
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    return $r
}

function VATA-Help {
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "VATA SDK - PowerShell Commands" -ForegroundColor Cyan
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
    Write-Host "VATA-Status        - System status"
    Write-Host "VATA-Metrics       - Proof metrics"
    Write-Host "VATA-ListProofs    - List all proofs"
    Write-Host "VATA-GetProof -Id  - Get proof by ID"
    Write-Host "VATA-SubmitProof   - Submit a single proof"
    Write-Host "VATA-SubmitBatch   - Submit a batch of proofs"
    Write-Host "VATA-Help          - Show this help"
    Write-Host "----------------------------------------------" -ForegroundColor DarkCyan
}

Write-Host "VATA SDK loaded. Type VATA-Help for commands." -ForegroundColor Cyan
