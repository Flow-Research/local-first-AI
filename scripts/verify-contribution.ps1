param(
    [string]$Root = "."
)

$ErrorActionPreference = "Stop"
$projectRoot = Resolve-Path $Root
$requiredPaths = @(
    "README.md",
    "PROJECT_BRIEF.md",
    "docs/roadmap.md",
    "docs/architecture.md",
    "docs/branching-and-features.md",
    "docs/research-and-design-architecture.md",
    "docs/documentation-guide.md",
    "CONTRIBUTING.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "features",
    "research",
    "design",
    "reports"
)

$failures = New-Object System.Collections.Generic.List[string]

foreach ($path in $requiredPaths) {
    $fullPath = Join-Path $projectRoot $path
    if (-not (Test-Path $fullPath)) {
        $failures.Add("Missing required path: $path")
    }
}

for ($month = 1; $month -le 12; $month++) {
    $monthName = "month-{0:D2}" -f $month
    $monthPath = Join-Path $projectRoot "reports/$monthName"
    if (-not (Test-Path $monthPath)) {
        $failures.Add("Missing report folder: reports/$monthName")
        continue
    }

    $projectReports = Get-ChildItem -Path $monthPath -Filter "*.md" -File |
        Where-Object { $_.Name -notmatch "^week-\d{2}-fellow-" }
    if ($projectReports.Count -ne 4) {
        $failures.Add("Expected 4 project week overviews in reports/$monthName but found $($projectReports.Count)")
    }
}

$allReports = Get-ChildItem -Path (Join-Path $projectRoot "reports") -Recurse -Filter "*.md" -File |
    Where-Object { $_.Name -ne "README.md" }
$projectWeeklyReports = $allReports |
    Where-Object { $_.Name -notmatch "^week-\d{2}-fellow-" }
$fellowWeeklyReports = $allReports |
    Where-Object { $_.Name -match "^week-\d{2}-fellow-" }

foreach ($report in $projectWeeklyReports) {
    $text = Get-Content -Path $report.FullName -Raw
    foreach ($section in @("Research / Learning", "Design Outcome", "Evidence")) {
        if ($text -notmatch [regex]::Escape($section)) {
            $relative = Resolve-Path -Path $report.FullName -Relative
            $failures.Add("Missing section '$section' in $relative")
        }
    }
}

foreach ($report in $fellowWeeklyReports) {
    $text = Get-Content -Path $report.FullName -Raw
    foreach ($section in @("Fellow:", "What I Did", "Commits", "Public Post", "Blocker or Next Step")) {
        if ($text -notmatch [regex]::Escape($section)) {
            $relative = Resolve-Path -Path $report.FullName -Relative
            $failures.Add("Missing field or section '$section' in $relative")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Verification failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host "- $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Verification passed: baseline structure, project reports, fellow updates, and contribution docs are present." -ForegroundColor Green
