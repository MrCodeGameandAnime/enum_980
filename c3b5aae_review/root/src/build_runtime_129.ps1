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
$projectPath = Join-Path $reviewRoot 'build/compat-129-core/ports/windows/micropython.vcxproj'
$propsPath = Join-Path $reviewRoot 'config/compat.props'
$logPath = Join-Path $reviewRoot 'results/runtime-129-build.log'
$oldTag = [Environment]::GetEnvironmentVariable('MICROPY_GIT_TAG', 'Process')
$oldHash = [Environment]::GetEnvironmentVariable('MICROPY_GIT_HASH', 'Process')
try {
    # A copied source tree must not inherit enum_980's parent Git identity.
    $env:MICROPY_GIT_TAG = 'v1.29.0-enum980-review'
    $env:MICROPY_GIT_HASH = '0fd6c573ea815774668bbb16b8e197c8822368b2+patched'
    & $MSBuild $projectPath /m /p:Configuration=Release /p:Platform=Win32 /p:PlatformToolset=v145 "/p:CustomPropsFile=$propsPath" "/p:PyPython=$Python" /verbosity:minimal *> $logPath
    $buildExit = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable('MICROPY_GIT_TAG', $oldTag, 'Process')
    [Environment]::SetEnvironmentVariable('MICROPY_GIT_HASH', $oldHash, 'Process')
}
Get-Content $logPath -Tail 20
if ($buildExit -ne 0) { exit $buildExit }
