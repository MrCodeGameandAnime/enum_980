param(
    [string]$Python = 'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
    [string]$MSBuild = ''
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'build_runtime_129.ps1') -Python $Python -MSBuild $MSBuild
exit $LASTEXITCODE
