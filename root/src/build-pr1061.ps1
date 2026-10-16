param(
    [string]$Python = 'python',
    [string]$MSBuild = 'MSBuild'
)
$ErrorActionPreference = 'Stop'
$rootPath = Split-Path -Parent $PSScriptRoot
$propsPath = Join-Path $rootPath 'config/pr1061.props'
$projectPath = Join-Path $rootPath 'build/pr1061/core/ports/windows/micropython.vcxproj'
$pythonPath = (Get-Command $Python).Source
$msbuildPath = (Get-Command $MSBuild).Source
& $msbuildPath $projectPath /m /p:Configuration=Release /p:Platform=Win32 /p:PlatformToolset=v145 "/p:CustomPropsFile=$propsPath" "/p:PyPython=$pythonPath" /verbosity:minimal
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
