<#
Moltbook Diff v2 (FULL FILE REPLACEMENT)
Compares the last two runs under .\runs\moltbook_*
Uses:
  - normalized\agents_derived.csv
  - normalized\search_posts.csv

Outputs (into .\diff\...):
  - agents_derived_new.csv
  - agents_derived_removed.csv
  - agents_derived_changed.csv   (mentions changed for same candidate)
  - search_query_counts.csv
  - diff_summary.json

Usage:
  pwsh -ExecutionPolicy Bypass -File .\scripts\moltbook_diff.ps1 -RunsDir ".\runs" -OutDir ".\diff"
#>

param(
  [string]$RunsDir = ".\runs",
  [string]$OutDir  = ".\diff"
)

$ErrorActionPreference = "Stop"

function Get-LatestRunDirs {
  param([string]$Root)
  if (-not (Test-Path $Root)) { throw "RunsDir not found: $Root" }

  $dirs = Get-ChildItem -Path $Root -Directory -Filter "moltbook_*" | Sort-Object Name
  if ($dirs.Count -lt 2) { throw "Need at least 2 run folders in $Root (found $($dirs.Count))." }

  $prev = $dirs[$dirs.Count - 2].FullName
  $last = $dirs[$dirs.Count - 1].FullName
  return @{ prev=$prev; last=$last }
}

function Read-CsvOrEmpty {
  param([string]$Path)
  if (Test-Path $Path) { return Import-Csv $Path }
  return @()
}

function Ensure-Dir {
  param([string]$Path)
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Index-ByKey {
  param($Rows, [string]$KeyField)
  $map = @{}
  foreach ($r in $Rows) {
    $k = $r.$KeyField
    if ([string]::IsNullOrWhiteSpace($k)) { continue }
    if (-not $map.ContainsKey($k)) { $map[$k] = $r }
  }
  return $map
}

function Count-ByQuery {
  param($Rows)
  $counts = @{}
  foreach ($r in $Rows) {
    $q = $r.query
    if ([string]::IsNullOrWhiteSpace($q)) { continue }
    if (-not $counts.ContainsKey($q)) { $counts[$q] = 0 }
    $counts[$q]++
  }
  return $counts
}

# --- locate runs ---
$runs = Get-LatestRunDirs -Root $RunsDir
$prevRun = $runs.prev
$lastRun = $runs.last

$prevId = Split-Path $prevRun -Leaf
$lastId = Split-Path $lastRun -Leaf

Write-Host "Prev: $prevId"
Write-Host "Last: $lastId"

# --- load data ---
$prevAgentsPath = Join-Path $prevRun "normalized\agents_derived.csv"
$lastAgentsPath = Join-Path $lastRun "normalized\agents_derived.csv"
$prevPostsPath  = Join-Path $prevRun "normalized\search_posts.csv"
$lastPostsPath  = Join-Path $lastRun "normalized\search_posts.csv"

$prevAgents = Read-CsvOrEmpty $prevAgentsPath
$lastAgents = Read-CsvOrEmpty $lastAgentsPath
$prevPosts  = Read-CsvOrEmpty $prevPostsPath
$lastPosts  = Read-CsvOrEmpty $lastPostsPath

if ($prevAgents.Count -eq 0) { Write-Warning "Prev agents_derived.csv empty or missing: $prevAgentsPath" }
if ($lastAgents.Count -eq 0) { Write-Warning "Last agents_derived.csv empty or missing: $lastAgentsPath" }

# --- prep output dir ---
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$diffDir = Join-Path $OutDir ("moltbook_diff_" + $prevId + "__to__" + $lastId + "__" + $stamp)
Ensure-Dir $diffDir

# --- derived agent diffs ---
# Key is 'candidate'
$prevMap = Index-ByKey $prevAgents "candidate"
$lastMap = Index-ByKey $lastAgents "candidate"

$prevKeys = New-Object System.Collections.Generic.HashSet[string]
$lastKeys = New-Object System.Collections.Generic.HashSet[string]
foreach ($k in $prevMap.Keys) { [void]$prevKeys.Add($k) }
foreach ($k in $lastMap.Keys) { [void]$lastKeys.Add($k) }

$newAgents = @()
$removedAgents = @()
$changedAgents = @()

foreach ($k in $lastKeys) {
  if (-not $prevKeys.Contains($k)) {
    $newAgents += [pscustomobject]@{
      run_id    = $lastId
      candidate = $k
      mentions  = [int]$lastMap[$k].mentions
    }
  }
}

foreach ($k in $prevKeys) {
  if (-not $lastKeys.Contains($k)) {
    $removedAgents += [pscustomobject]@{
      run_id    = $prevId
      candidate = $k
      mentions  = [int]$prevMap[$k].mentions
    }
  }
}

foreach ($k in $lastKeys) {
  if ($prevKeys.Contains($k)) {
    $mPrev = [int]$prevMap[$k].mentions
    $mLast = [int]$lastMap[$k].mentions
    if ($mPrev -ne $mLast) {
      $changedAgents += [pscustomobject]@{
        candidate    = $k
        prev_mentions = $mPrev
        last_mentions = $mLast
        delta         = ($mLast - $mPrev)
      }
    }
  }
}

# --- search query hit diffs (counts per query) ---
$prevCounts = Count-ByQuery $prevPosts
$lastCounts = Count-ByQuery $lastPosts

$allQueries = New-Object System.Collections.Generic.HashSet[string]
foreach ($k in $prevCounts.Keys) { [void]$allQueries.Add($k) }
foreach ($k in $lastCounts.Keys) { [void]$allQueries.Add($k) }

$queryDiff = @()
foreach ($q in ($allQueries | Sort-Object)) {
  $p = 0; $l = 0
  if ($prevCounts.ContainsKey($q)) { $p = [int]$prevCounts[$q] }
  if ($lastCounts.ContainsKey($q)) { $l = [int]$lastCounts[$q] }
  $queryDiff += [pscustomobject]@{
    query = $q
    prev  = $p
    last  = $l
    delta = ($l - $p)
  }
}

# --- write outputs ---
$newCsv  = Join-Path $diffDir "agents_derived_new.csv"
$remCsv  = Join-Path $diffDir "agents_derived_removed.csv"
$chgCsv  = Join-Path $diffDir "agents_derived_changed.csv"
$qryCsv  = Join-Path $diffDir "search_query_counts.csv"

$newAgents     | Sort-Object mentions -Descending | Export-Csv -NoTypeInformation -Encoding utf8 $newCsv
$removedAgents | Sort-Object mentions -Descending | Export-Csv -NoTypeInformation -Encoding utf8 $remCsv
$changedAgents | Sort-Object delta -Descending    | Export-Csv -NoTypeInformation -Encoding utf8 $chgCsv
$queryDiff     | Sort-Object delta -Descending    | Export-Csv -NoTypeInformation -Encoding utf8 $qryCsv

# --- summary ---
$summary = [pscustomobject]@{
  prev_run = $prevId
  last_run = $lastId

  derived_prev_count = $prevAgents.Count
  derived_last_count = $lastAgents.Count
  derived_new_count = $newAgents.Count
  derived_removed_count = $removedAgents.Count
  derived_changed_count = $changedAgents.Count

  search_prev_count = $prevPosts.Count
  search_last_count = $lastPosts.Count

  diff_dir = $diffDir
  inputs = [pscustomobject]@{
    prev_agents_derived = $prevAgentsPath
    last_agents_derived = $lastAgentsPath
    prev_search_posts   = $prevPostsPath
    last_search_posts   = $lastPostsPath
  }
  outputs = @(
    "agents_derived_new.csv"
    "agents_derived_removed.csv"
    "agents_derived_changed.csv"
    "search_query_counts.csv"
    "diff_summary.json"
  )
}

$summaryPath = Join-Path $diffDir "diff_summary.json"
$summary | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 $summaryPath

Write-Host "`n=== DIFF SUMMARY ==="
$summary | Format-List | Out-String | Write-Host

Write-Host "`nOutputs:"
Write-Host "  $newCsv"
Write-Host "  $remCsv"
Write-Host "  $chgCsv"
Write-Host "  $qryCsv"
Write-Host "  $summaryPath"
