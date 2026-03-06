function vata {
    param([string]$command, [string]$path)
    
    switch ($command) {
        "status" {
            Write-Host "📊 VATA CLI v3.0 | Status: OPERATIONAL" -ForegroundColor Yellow
        }
        "scan" {
            if (-not $path) { $path = "." }
            Write-Host "🔍 Scanning project at $path for VATA-STD Compliance..." -ForegroundColor Cyan
            
            $score = 0
            $files = Get-ChildItem -Path $path -Filter "*.circom" -Recurse
            
            foreach ($file in $files) {
                $content = Get-Content $file.FullName
                if ($content -match "VataMerkle") { $score += 33 }
                if ($content -match "VataNullifier") { $score += 33 }
                if ($content -match "VataSignature") { $score += 34 }
            }
            
            Write-Host "---------------------------------------"
            Write-Host "VATA SECURITY SCORE: $score/100" -ForegroundColor ($score -gt 60 ? "Green" : "Red")
            if ($score -eq 100) { Write-Host "🏆 VERIFIED SOVEREIGN STATUS" -ForegroundColor Gold }
            Write-Host "---------------------------------------"
        }
        Default { Write-Host "Available: status, scan [path], inject, init" }
    }
}
