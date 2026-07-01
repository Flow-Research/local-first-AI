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

    $reportCount = (Get-ChildItem -Path $monthPath -Filter "*.md" -File).Count
    if ($reportCount -ne 4) {
        $failures.Add("Expected 4 weekly reports in reports/$monthName but found $reportCount")
    }
}

$weeklyReports = Get-ChildItem -Path (Join-Path $projectRoot "reports") -Recurse -Filter "*.md" -File |
    Where-Object { $_.Name -ne "README.md" }

foreach ($report in $weeklyReports) {
    $text = Get-Content -Path $report.FullName -Raw
    $usesLegacyFormat = $text -match "Research / Learning" -and
        $text -match "Design Outcome" -and
        $text -match "Evidence"
    $fellowBlocks = [regex]::Matches(
        $text,
        "(?ms)^## Fellow \d+:[^\r\n]*\r?\n(?<block>.*?)(?=^## Fellow \d+:|\z)"
    )
    $usesFellowFormat = $fellowBlocks.Count -gt 0

    if (-not $usesFellowFormat -and -not $usesLegacyFormat) {
        $relative = Resolve-Path -Path $report.FullName -Relative
        $failures.Add("Weekly report must use the fellow format in $relative")
        continue
    }

    if ($usesFellowFormat) {
        $blockNumber = 0
        foreach ($fellowBlock in $fellowBlocks) {
            $blockNumber++
            $block = $fellowBlock.Groups["block"].Value
            $relative = Resolve-Path -Path $report.FullName -Relative

            if ($block -notmatch "(?m)^\s*-\s+\*\*Topic:\*\*\s+\S") {
                $failures.Add("Missing topic in fellow block $blockNumber of $relative")
            }

            if ($block -notmatch "(?m)^\s*-\s+\*\*Public output:\*\*\s+\S") {
                $failures.Add("Missing public output in fellow block $blockNumber of $relative")
            }

            $workMatch = [regex]::Match(
                $block,
                "(?ms)^\s*-\s+\*\*What I did:\*\*\s*(?<work>.*?)(?=^\s*-\s+\*\*Public output:\*\*)"
            )
            if (-not $workMatch.Success) {
                $failures.Add("Missing 'What I did' in fellow block $blockNumber of $relative")
                continue
            }

            $work = $workMatch.Groups["work"].Value
            $wordCount = [regex]::Matches(
                $work,
                "\b[\p{L}\p{N}][\p{L}\p{N}'’-]*\b"
            ).Count
            if ($wordCount -lt 20) {
                $failures.Add(
                    "'What I did' needs at least 20 words in fellow block $blockNumber of $relative; found $wordCount"
                )
            }
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

Write-Host "Verification passed: baseline structure, weekly reports, and contribution docs are present." -ForegroundColor Green
