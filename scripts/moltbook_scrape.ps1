<# 
Moltbook Scrape v2
- Multi-endpoint scrape
- Saves raw JSON + normalized CSV
- Creates timestamped run folder for diffing later

Usage:
  pwsh -ExecutionPolicy Bypass -File .\scripts\moltbook_scrape.ps1 -BaseUrl "https://www.moltbook.com" -OutDir ".\runs"
#>

param(
  [string]$BaseUrl = "https://www.moltbook.com",
  [string]$OutDir  = ".\runs",
  [int]$Limit = 50,
  [int]$DelayMs = 250
)

$ErrorActionPreference = "Stop"

function New-RunDir {
  param([string]$Root)
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $dir = Join-Path $Root ("moltbook_" + $ts)
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  return $dir
}

function Invoke-JsonGet {
  param(
    [string]$Url,
    [string]$OutPath
  )
  Write-Host "GET $Url"
  try {
    $resp = Invoke-RestMethod -Uri $Url -Method GET -Headers @{ "User-Agent" = "Mozilla/5.0" } -TimeoutSec 30
    $resp | ConvertTo-Json -Depth 25 | Out-File -Encoding utf8 $OutPath
    return $resp
  } catch {
    $msg = $_.Exception.Message
    Write-Warning "FAILED: $Url :: $msg"
    @{ "__error" = $true; "url" = $Url; "message" = $msg } | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $OutPath
    return $null
  } finally {
    Start-Sleep -Milliseconds $DelayMs
  }
}

function Export-FlatCsv {
  param(
    [object[]]$Rows,
    [string]$CsvPath
  )
  if (-not $Rows -or $Rows.Count -eq 0) {
    Write-Warning "No rows to export: $CsvPath"
    return
  }
  $Rows | Export-Csv -NoTypeInformation -Encoding utf8 $CsvPath
}

# --- Run directory ---
$runDir = New-RunDir -Root $OutDir
Write-Host "Run dir: $runDir"

# --- Endpoint plan ---
# NOTE: These are conservative guesses based on common Moltbook patterns you used earlier.
# If any endpoint returns 404 or Cloudflare blocks, it will be logged but the run continues.

$endpoints = @(
  @{ name="insights_view"; url="$BaseUrl/_vercel/insights/view" ; type="raw" },
  @{ name="agents_profile_grok_1"; url="$BaseUrl/api/v1/agents/profile?name=grok-1" ; type="raw" },
  @{ name="agents_discover_grok_1"; url="$BaseUrl/api/v1/agents/grok-1/discover" ; type="raw" },
  @{ name="agents_list"; url="$BaseUrl/api/v1/agents?limit=$Limit" ; type="agents" },

  # Searches (tune keywords as desired)
  @{ name="search_agent"; url="$BaseUrl/api/v1/search?q=agent&type=all&limit=$Limit" ; type="search" },
  @{ name="search_orchestrator"; url="$BaseUrl/api/v1/search?q=orchestrator&type=all&limit=$Limit" ; type="search" },
  @{ name="search_bot"; url="$BaseUrl/api/v1/search?q=bot&type=all&limit=$Limit" ; type="search" },
  @{ name="search_swarm"; url="$BaseUrl/api/v1/search?q=swarm&type=all&limit=$Limit" ; type="search" },
  @{ name="search_ai"; url="$BaseUrl/api/v1/search?q=ai&type=all&limit=$Limit" ; type="search" }
)

# --- Storage ---
$rawDir = Join-Path $runDir "raw"
$normDir = Join-Path $runDir "normalized"
New-Item -ItemType Directory -Force -Path $rawDir, $normDir | Out-Null

# --- Normalized collections ---
$agentsRows = New-Object System.Collections.Generic.List[object]
$postsRows  = New-Object System.Collections.Generic.List[object]

foreach ($ep in $endpoints) {
  $jsonPath = Join-Path $rawDir ($ep.name + ".json")
  $data = Invoke-JsonGet -Url $ep.url -OutPath $jsonPath
  if ($null -eq $data) { continue }

  if ($ep.type -eq "agents") {
    # Attempt to normalize "agents list" response.
    # Handles either {items:[...]} or direct array [...]
    $items = $null
    if ($data.items) { $items = $data.items }
    elseif ($data.data) { $items = $data.data }
    elseif ($data -is [System.Collections.IEnumerable]) { $items = $data }
    else { $items = @() }

    foreach ($a in $items) {
      # Best-effort extraction (fields may vary)
      $name = $a.name
      if (-not $name -and $a.profile -and $a.profile.name) { $name = $a.profile.name }

      $agentsRows.Add([pscustomobject]@{
        run_id     = (Split-Path $runDir -Leaf)
        source     = $ep.name
        name       = $name
        id         = $a.id
        handle     = $a.handle
        model      = $a.model
        created_at = $a.created_at
        updated_at = $a.updated_at
        raw_hint   = ($a | ConvertTo-Json -Depth 5 -Compress)
      })
    }
  }

  if ($ep.type -eq "search") {
    # Normalize search results into "posts" style rows.
    $items = $null
    if ($data.items) { $items = $data.items }
    elseif ($data.results) { $items = $data.results }
    elseif ($data.data) { $items = $data.data }
    elseif ($data -is [System.Collections.IEnumerable]) { $items = $data }
    else { $items = @() }

    foreach ($p in $items) {
      $postsRows.Add([pscustomobject]@{
        run_id     = (Split-Path $runDir -Leaf)
        source     = $ep.name
        query      = ($ep.name -replace "^search_", "")
        post_id    = $p.id
        author     = $p.author
        title      = $p.title
        created_at = $p.created_at
        url        = $p.url
        snippet    = $p.snippet
        raw_hint   = ($p | ConvertTo-Json -Depth 5 -Compress)
      })
    }
  }
}

# --- Export normalized outputs ---
$agentsCsv = Join-Path $normDir "agents.csv"
$postsCsv  = Join-Path $normDir "search_posts.csv"

Export-FlatCsv -Rows $agentsRows -CsvPath $agentsCsv
Export-FlatCsv -Rows $postsRows  -CsvPath $postsCsv

# --- Manifest ---
$manifest = [pscustomobject]@{
  run_id     = (Split-Path $runDir -Leaf)
  base_url   = $BaseUrl
  limit      = $Limit
  delay_ms   = $DelayMs
  created_at = (Get-Date).ToString("o")
  files      = @(
    @{ path = "raw\" + "/*.json" },
    @{ path = "normalized\agents.csv" },
    @{ path = "normalized\search_posts.csv" }
  )
}

$manifestPath = Join-Path $runDir "run_manifest.json"
$manifest | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $manifestPath

Write-Host "`nDONE."
Write-Host "Raw:        $rawDir"
Write-Host "Normalized: $normDir"
Write-Host "Manifest:   $manifestPath"
