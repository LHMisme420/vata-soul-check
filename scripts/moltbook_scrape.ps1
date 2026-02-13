
<# 
Moltbook Scrape v2.3 (FULL FILE REPLACEMENT)
- Uses only endpoints that have worked:
    - /api/v1/agents/profile?name=<seed>
    - /api/v1/agents/<seed>/discover
    - /api/v1/search?q=<query>&type=all&limit=<n>
- Saves raw responses to runs\<run>\raw\*.json
- Normalizes search results to runs\<run>\normalized\search_posts.csv
- Derives agent-like candidates to runs\<run>\normalized\agents_derived.csv

Derivation improvements:
- Extracts from author/title/snippet/raw_hint
- Supports:
    - underscore handles: Foo_Bar_123
    - hyphen handles: foo-bar-123
    - alnum handles: Agent007, NebulaBot2026
- Filters obvious junk (common words + very short tokens)
- Counts mentions

Usage:
  pwsh -ExecutionPolicy Bypass -File .\scripts\moltbook_scrape.ps1 -BaseUrl "https://www.moltbook.com" -OutDir ".\runs" -Limit 50 -DelayMs 250
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
    $headers = @{
      "User-Agent" = "Mozilla/5.0"
      "Accept"     = "application/json,text/plain,*/*"
      "Referer"    = "https://www.moltbook.com/"
    }

    $r = Invoke-WebRequest -Uri $Url -Method GET -Headers $headers -TimeoutSec 30 -UseBasicParsing
    $r.Content | Out-File -Encoding utf8 $OutPath

    $trim = $r.Content.Trim()
    if ($trim.StartsWith("{") -or $trim.StartsWith("[")) {
      return ($r.Content | ConvertFrom-Json -Depth 50)
    }

    Write-Warning "Non-JSON response saved to $OutPath (likely blocked/WAF/HTML)."
    return $null
  } catch {
    $msg = $_.Exception.Message
    Write-Warning "FAILED: $Url :: $msg"
    @{ "__error" = $true; "url" = $Url; "message" = $msg } |
      ConvertTo-Json -Depth 5 |
      Out-File -Encoding utf8 $OutPath
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

# -------------------------
# RUN DIRECTORY STRUCTURE
# -------------------------
$runDir = New-RunDir -Root $OutDir
Write-Host "Run dir: $runDir"

$rawDir  = Join-Path $runDir "raw"
$normDir = Join-Path $runDir "normalized"
New-Item -ItemType Directory -Force -Path $rawDir, $normDir | Out-Null

# -------------------------
# ENDPOINTS
# -------------------------
$seedAgents = @(
  "grok-1"
  # Add more seeds as you discover them:
  # "NebulaBot2026"
  # "DeutschBot_Elite_383"
)

$endpoints = @()

foreach ($a in $seedAgents) {
  $endpoints += @{ name=("agents_profile_" + $a);  url="$BaseUrl/api/v1/agents/profile?name=$a" ; type="raw" }
  $endpoints += @{ name=("agents_discover_" + $a); url="$BaseUrl/api/v1/agents/$a/discover" ; type="raw" }
}

# Expanded neutral queries (high yield, low noise)
$queries = @(
  "agent","agents","profile","discover","orchestrator","orchestration",
  "bot","swarm","ai","model","api","grok-1"
)

foreach ($q in $queries) {
  $safe = $q -replace "[^a-zA-Z0-9_-]","_"
  $endpoints += @{ name=("search_" + $safe); url="$BaseUrl/api/v1/search?q=$q&type=all&limit=$Limit" ; type="search" }
}

# -------------------------
# NORMALIZED SEARCH ROWS
# -------------------------
$postsRows = New-Object System.Collections.Generic.List[object]

foreach ($ep in $endpoints) {
  $jsonPath = Join-Path $rawDir ($ep.name + ".json")
  $data = Invoke-JsonGet -Url $ep.url -OutPath $jsonPath
  if ($null -eq $data) { continue }

  if ($ep.type -eq "search") {
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
        raw_hint   = ($p | ConvertTo-Json -Depth 8 -Compress)
      })
    }
  }
}

# -------------------------
# DERIVE AGENT-LIKE CANDIDATES (IMPROVED)
# -------------------------
# Heuristic: we want "handle-ish" tokens, not normal words.
# We collect candidates and count mentions.

# Common words to ignore (extend as needed)
$stop = @(
  "the","and","for","with","from","that","this","you","your","they","them","are","was","were",
  "have","has","had","not","but","can","will","just","like","into","out","over","under","more",
  "less","about","what","when","where","who","why","how","all","any","new","old","good","bad",
  "agent","agents","bot","bots","swarm","ai","api","model","profile","discover","orchestrator","orchestration"
) | ForEach-Object { $_.ToLowerInvariant() }

$stopSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($w in $stop) { [void]$stopSet.Add($w) }

# Patterns:
# 1) underscore handles: Foo_Bar_123
$reUnderscore = [regex]"\b[A-Za-z][A-Za-z0-9]+(?:_[A-Za-z0-9]+){1,6}\b"
# 2) hyphen handles: foo-bar-123
$reHyphen     = [regex]"\b[a-zA-Z][a-zA-Z0-9]+(?:-[a-zA-Z0-9]+){1,6}\b"
# 3) alnum handles: Agent007, NebulaBot2026, ClawdTradingBot
$reAlnum      = [regex]"\b[A-Za-z]{3,}[A-Za-z0-9]{2,}\b"

function Add-Candidate {
  param([hashtable]$Map, [string]$Token)

  if ([string]::IsNullOrWhiteSpace($Token)) { return }

  # normalize
  $t = $Token.Trim()
  if ($t.Length -lt 4) { return }              # too short
  if ($t.Length -gt 40) { return }             # too long (often junk)
  if ($t -match "^[0-9]+$") { return }         # numbers only

  $low = $t.ToLowerInvariant()
  if ($stopSet.Contains($low)) { return }

  # Avoid generic words that match reAlnum (e.g. "CreatedAt")
  if ($low -match "^(created|updated|commit|manifest|normalized|snippet|title|author|search|posts)$") { return }

  if (-not $Map.ContainsKey($t)) { $Map[$t] = 0 }
  $Map[$t]++
}

$derived = @{}

foreach ($r in $postsRows) {
  $txt = @($r.author, $r.title, $r.snippet, $r.raw_hint) -join " "

  foreach ($m in $reUnderscore.Matches($txt)) { Add-Candidate -Map $derived -Token $m.Value }
  foreach ($m in $reHyphen.Matches($txt))     { Add-Candidate -Map $derived -Token $m.Value }

  # For alnum pattern, be stricter: require either digits OR mixed-case (common bot naming)
  foreach ($m in $reAlnum.Matches($txt)) {
    $tok = $m.Value
    $hasDigit = ($tok -match "\d")
    $hasUpper = ($tok -cmatch "[A-Z]") # case-sensitive match
    if ($hasDigit -or $hasUpper) {
      Add-Candidate -Map $derived -Token $tok
    }
  }
}

$derivedRows = @()
foreach ($k in $derived.Keys) {
  $derivedRows += [pscustomobject]@{
    run_id     = (Split-Path $runDir -Leaf)
    candidate  = $k
    mentions   = [int]$derived[$k]
  }
}
$derivedRows = $derivedRows | Sort-Object mentions -Descending

# -------------------------
# EXPORT NORMALIZED OUTPUTS
# -------------------------
$postsCsv   = Join-Path $normDir "search_posts.csv"
$derivedCsv = Join-Path $normDir "agents_derived.csv"

Export-FlatCsv -Rows $postsRows   -CsvPath $postsCsv
Export-FlatCsv -Rows $derivedRows -CsvPath $derivedCsv

# -------------------------
# MANIFEST
# -------------------------
$manifest = [pscustomobject]@{
  run_id     = (Split-Path $runDir -Leaf)
  base_url   = $BaseUrl
  limit      = $Limit
  delay_ms   = $DelayMs
  created_at = (Get-Date).ToString("o")
  seed_agents = $seedAgents
  queries     = $queries
  outputs    = @(
    "normalized\search_posts.csv"
    "normalized\agents_derived.csv"
  )
}

$manifestPath = Join-Path $runDir "run_manifest.json"
$manifest | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $manifestPath

Write-Host "`nDONE."
Write-Host "Raw:        $rawDir"
Write-Host "Normalized: $normDir"
Write-Host "Manifest:   $manifestPath"
Write-Host "`nNext:"
Write-Host "  1) Run another scrape (so you have two v2.3 runs)"
Write-Host "  2) Run diff: pwsh -ExecutionPolicy Bypass -File .\scripts\moltbook_diff.ps1 -RunsDir .\runs -OutDir .\diff"
