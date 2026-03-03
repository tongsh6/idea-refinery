#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "../..")
$PythonScript = Join-Path $ProjectRoot "scripts/release/gitflow_release.py"

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $Python = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
} else {
    throw "Python interpreter not found (python3/python)."
}

& $Python $PythonScript @args
exit $LASTEXITCODE
