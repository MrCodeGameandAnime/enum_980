param(
    [string]$Python = 'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
    [string]$MSBuild = ''
)
$ErrorActionPreference = 'Stop'
$reviewRoot = Split-Path -Parent $PSScriptRoot
if (-not $MSBuild) {
    $locator = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
    $MSBuild = & $locator -latest -products '*' -requires Microsoft.Component.MSBuild -find 'MSBuild/**/Bin/MSBuild.exe' | Select-Object -First 1
}
if (-not $MSBuild) { throw 'MSBuild was not found' }
$projectPath = Join-Path $reviewRoot 'build/compat-core/ports/windows/micropython.vcxproj'
$propsPath = Join-Path $reviewRoot 'config/compat.props'
$logPath = Join-Path $reviewRoot 'results/compat-build.log'
& $MSBuild $projectPath /m /p:Configuration=Release /p:Platform=Win32 /p:PlatformToolset=v145 "/p:CustomPropsFile=$propsPath" "/p:PyPython=$Python" /verbosity:minimal *> $logPath
$buildExit = $LASTEXITCODE
Get-Content $logPath -Tail 20
if ($buildExit -ne 0) { exit $buildExit }
