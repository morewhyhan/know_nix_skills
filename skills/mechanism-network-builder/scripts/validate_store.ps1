param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)

$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'validate_store.py'

$candidates = @()
$python3 = Get-Command python3 -ErrorAction SilentlyContinue
if ($python3 -and $python3.Source -notmatch 'WindowsApps') { $candidates += $python3.Source }

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python -and $python.Source -notmatch 'WindowsApps') { $candidates += $python.Source }

$bundled = Join-Path $HOME '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundled) { $candidates += $bundled }

$candidates = @($candidates | Select-Object -Unique)
if ($candidates.Count -eq 0) {
    throw 'No usable Python 3 runtime found.'
}

$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
& $candidates[0] $script --root $Root
exit $LASTEXITCODE
