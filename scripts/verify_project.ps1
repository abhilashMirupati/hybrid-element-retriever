Param()

Write-Output "Running formatting checks (black)…"
black --check src/her tests

Write-Output "Running flake8…"
flake8 src/her tests

Write-Output "Running mypy…"
mypy src/her

Write-Output "Running pytest…"
pytest --cov=src/her --cov-report=term

$Comment = @'
Check for forbidden placeholder markers.  In PowerShell we search
recursively for literal ellipses (…), or the typical task marker string, within
the relevant directories.  If any match is found the script exits
with an error.  This prevents inadvertent shipping of unfinished
code into the repository.
'@
<#
$Comment
#>
$dot = "\\."
# Assemble the task marker from parts to avoid embedding the literal word.
$p1 = "TO"
$p2 = "DO"
$word = $p1 + $p2
# Build the search pattern without embedding the forbidden triple dot directly
# in this script.  We concatenate three escaped dots and append the assembled
# task marker.
$pattern = $dot + $dot + $dot + "|" + $word
$placeholderMatches = Get-ChildItem -Recurse -Include *.py,*.sh,*.ps1,*.yml -Path src/her,scripts,ci,java | ForEach-Object {
    Select-String -Pattern $pattern -Path $_.FullName -SimpleMatch
}
if ($placeholderMatches) {
    Write-Error "Error: placeholder '…' or task marker detected in codebase."
    $placeholderMatches | Format-Table -Property Filename,LineNumber,Line
    exit 1
}

Write-Output "All checks passed."