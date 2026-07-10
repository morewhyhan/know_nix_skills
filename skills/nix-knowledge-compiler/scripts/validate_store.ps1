[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Root
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$validatorPath = [System.IO.Path]::GetFullPath(
    (Join-Path -Path $PSScriptRoot -ChildPath 'validate_store.py')
)
if (-not (Test-Path -LiteralPath $validatorPath -PathType Leaf)) {
    [Console]::Error.WriteLine("Validator not found: $validatorPath")
    exit 2
}

if ([System.IO.Path]::IsPathRooted($Root)) {
    $rootPath = [System.IO.Path]::GetFullPath($Root)
}
else {
    $rootPath = [System.IO.Path]::GetFullPath(
        (Join-Path -Path (Get-Location).Path -ChildPath $Root)
    )
}

function Test-PythonRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,
        [string[]]$PrefixArguments = @()
    )

    try {
        & $Executable @PrefixArguments '-B' '-X' 'utf8' '-c' `
            'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' `
            *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Test-WslPythonRuntime {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WslExecutable
    )

    try {
        & $WslExecutable 'python3' '-B' '-c' `
            'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' `
            *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

# Codex can expose its bundled workspace runtime through different variables
# across desktop versions. Probe all known explicit locations before PATH.
$bundledCandidates = [System.Collections.Generic.List[string]]::new()
$bundledFileVariables = @(
    'CODEX_PYTHON',
    'CODEX_PYTHON_PATH',
    'CODEX_BUNDLED_PYTHON',
    'CODEX_WORKSPACE_PYTHON',
    'OPENAI_CODEX_PYTHON',
    'OPENAI_BUNDLED_PYTHON',
    'WORKSPACE_PYTHON'
)
foreach ($variableName in $bundledFileVariables) {
    $value = [Environment]::GetEnvironmentVariable($variableName)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
        $bundledCandidates.Add($value)
    }
}

$runtimeRoots = [System.Collections.Generic.List[string]]::new()
$runtimeRootVariables = @(
    'CODEX_WORKSPACE_DEPENDENCIES',
    'CODEX_RUNTIME_ROOT',
    'CODEX_BUNDLED_RUNTIME',
    'OPENAI_CODEX_RUNTIME'
)
foreach ($variableName in $runtimeRootVariables) {
    $value = [Environment]::GetEnvironmentVariable($variableName)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
        $runtimeRoots.Add($value)
    }
}

$codexHome = [Environment]::GetEnvironmentVariable('CODEX_HOME')
if ([string]::IsNullOrWhiteSpace($codexHome) -and -not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    $codexHome = Join-Path -Path $env:USERPROFILE -ChildPath '.codex'
}
if (-not [string]::IsNullOrWhiteSpace($codexHome)) {
    $runtimeRoots.Add((Join-Path -Path $codexHome -ChildPath 'runtime'))
    $runtimeRoots.Add((Join-Path -Path $codexHome -ChildPath 'runtimes'))
    $runtimeRoots.Add((Join-Path -Path $codexHome -ChildPath 'workspace-dependencies'))
    $runtimeRoots.Add((Join-Path -Path $codexHome -ChildPath 'workspace_dependencies'))
}

if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    $bundledCandidates.Add((Join-Path -Path $env:USERPROFILE -ChildPath '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'))
}

if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $runtimeRoots.Add((Join-Path -Path $env:LOCALAPPDATA -ChildPath 'OpenAI\Codex\runtime'))
    $runtimeRoots.Add((Join-Path -Path $env:LOCALAPPDATA -ChildPath 'OpenAI\Codex\runtimes'))
}

try {
    foreach ($package in @(Get-AppxPackage -Name 'OpenAI.Codex*' -ErrorAction SilentlyContinue)) {
        if (-not [string]::IsNullOrWhiteSpace($package.InstallLocation)) {
            $runtimeRoots.Add((Join-Path -Path $package.InstallLocation -ChildPath 'app\resources'))
        }
    }
}
catch {
    # App package discovery is optional; explicit paths and PATH probes remain.
}

foreach ($runtimeRoot in @($runtimeRoots)) {
    if ([string]::IsNullOrWhiteSpace($runtimeRoot)) {
        continue
    }
    foreach ($relativePath in @(
        'python.exe',
        'python3.exe',
        'python\python.exe',
        'python\python3.exe',
        'bin\python.exe',
        'bin\python3.exe',
        'workspace_dependencies\python\python.exe',
        'workspace-dependencies\python\python.exe'
    )) {
        $bundledCandidates.Add((Join-Path -Path $runtimeRoot -ChildPath $relativePath))
    }
}

$seenBundled = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
$runtime = $null
foreach ($candidate in @($bundledCandidates)) {
    if ([string]::IsNullOrWhiteSpace($candidate) -or -not $seenBundled.Add($candidate)) {
        continue
    }
    try {
        if ((Test-Path -LiteralPath $candidate -PathType Leaf) -and
            (Test-PythonRuntime -Executable $candidate)) {
            $runtime = [pscustomobject]@{
                Kind = 'Windows'
                Name = 'Codex bundled Python'
                Executable = $candidate
                PrefixArguments = @()
            }
            break
        }
    }
    catch {
        # An inaccessible or stale runtime candidate is simply skipped.
    }
}

if ($null -eq $runtime) {
    foreach ($commandName in @('py', 'python3', 'python')) {
        $command = Get-Command $commandName -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -eq $command) {
            continue
        }
        $prefixArguments = if ($commandName -eq 'py') { @('-3') } else { @() }
        if (Test-PythonRuntime -Executable $command.Source -PrefixArguments $prefixArguments) {
            $runtime = [pscustomobject]@{
                Kind = 'Windows'
                Name = $commandName
                Executable = $command.Source
                PrefixArguments = $prefixArguments
            }
            break
        }
    }
}

if ($null -ne $runtime) {
    Write-Verbose "Using $($runtime.Name): $($runtime.Executable)"
    $arguments = @($runtime.PrefixArguments) + @(
        '-B',
        '-X',
        'utf8',
        $validatorPath,
        $rootPath
    )
    $windowsPython = $runtime.Executable
    & $windowsPython @arguments
    exit [int]$LASTEXITCODE
}

$wslCommand = Get-Command 'wsl.exe' -CommandType Application -ErrorAction SilentlyContinue |
    Select-Object -First 1
$wslExecutable = if ($null -ne $wslCommand) { $wslCommand.Source } else { $null }
if ($null -ne $wslCommand -and
    (Test-WslPythonRuntime -WslExecutable $wslExecutable)) {
    try {
        # Backslashes are consumed by WSL's command-line parser. Forward-slash
        # Windows paths preserve spaces and Unicode while remaining valid input
        # to wslpath (for example C:/Users/... instead of C:\Users\...).
        $validatorForWsl = $validatorPath.Replace('\', '/')
        $convertedValidator = @(
            & $wslExecutable 'wslpath' '-a' '--' $validatorForWsl
        )
        if ($LASTEXITCODE -ne 0 -or $convertedValidator.Count -eq 0) {
            throw "wslpath could not convert validator path"
        }
        $wslValidatorPath = $convertedValidator[0].Trim()
        if ([string]::IsNullOrWhiteSpace($wslValidatorPath)) {
            throw "wslpath returned an empty validator path"
        }

        $rootForWsl = $rootPath.Replace('\', '/')
        $convertedRoot = @(
            & $wslExecutable 'wslpath' '-a' '--' $rootForWsl
        )
        if ($LASTEXITCODE -ne 0 -or $convertedRoot.Count -eq 0) {
            throw "wslpath could not convert root path"
        }
        $wslRootPath = $convertedRoot[0].Trim()
        if ([string]::IsNullOrWhiteSpace($wslRootPath)) {
            throw "wslpath returned an empty root path"
        }
    }
    catch {
        [Console]::Error.WriteLine("Unable to convert paths for WSL: $($_.Exception.Message)")
        exit 2
    }

    Write-Verbose "Using WSL python3: $wslValidatorPath"
    & $wslExecutable 'python3' '-B' $wslValidatorPath $wslRootPath
    exit [int]$LASTEXITCODE
}

[Console]::Error.WriteLine(
    'No runnable Python 3 runtime was found in the Codex bundle, py, python3, python, or WSL.'
)
exit 127
