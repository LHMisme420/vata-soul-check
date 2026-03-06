while ($true) {
    $files = Get-ChildItem "C:\Users\lhmsi\zk-saas\inbox\*.circom"
    foreach ($file in $files) {
        Write-Host "[INCOMING] Processing $($file.Name)..." -ForegroundColor Cyan
        # Your AI logic would be called here
        Move-Item $file.FullName "C:\Users\lhmsi\zk-saas\processed\" -Force
        Write-Host "✅ Audit Finished." -ForegroundColor Green
    }
    Start-Sleep -Seconds 5
}
