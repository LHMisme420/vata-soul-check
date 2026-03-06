# Load the CSV
$data = Import-Csv "audit_log.csv"
$targetIndex = 42 # Change this to prove a different row!
$salt = "987654321" # Keep this secret!

# Extract values into an array
$values = $data.Value
$targetValue = $values[$targetIndex]

# Build the JSON object
$inputObj = @{
    "event_values" = $values
    "event_index"  = $targetIndex
    "event_value"  = $targetValue
    "salt"         = $salt
}

# Save it
$inputObj | ConvertTo-Json -Compress | Out-File -FilePath "input.json" -Encoding UTF8
Write-Host "📂 Prepared input.json for Index $targetIndex (Value: $targetValue)" -ForegroundColor Green
