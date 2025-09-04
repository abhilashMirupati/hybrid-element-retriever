param()

$ErrorActionPreference = "Stop"
Write-Host "=== HER repo cleanup ==="

$targets = @(
    # top-level docs / config
    ".coveragerc",".flake8","CHANGELOG.md","COMPONENTS_MATRIX.md","CONTRIBUTING.md",
    "GUIDE.md","PERF_REPORT.md","RELEASE_GATE.md","RISKS.md","SCORING_NOTES.md","TODO_LIST.md",
    # infrastructure
    ".github","docs","ci","samples","functional_harness","tests",
    # dev scripts
    "scripts/verify_parts.py","scripts/verify_project.ps1","scripts/verify_project.sh",
    "scripts/run_functional_validation.py",
    # legacy modules
    "src/her/promotion.py",
    "src/her/resilience.py",
    "src/her/runtime/",
    "src/her/session/",
    "src/her/validators.py",
    "src/her/config.py",
    "src/her/db.py",
    "src/her/utils/",
    "src/her/descriptors/merge.py"
)

$removed = 0; $skipped = 0
foreach ($rel in $targets) {
    $p = Join-Path -Path $PSScriptRoot -ChildPath $rel
    if (Test-Path $p) {
        Write-Host ("Removing: {0}" -f $rel)
        Remove-Item -LiteralPath $p -Recurse -Force
        $removed++
    } else {
        Write-Host ("Skip (not found): {0}" -f $rel)
        $skipped++
    }
}

Write-Host ("Done. Removed: {0}, Skipped: {1}" -f $removed, $skipped)
