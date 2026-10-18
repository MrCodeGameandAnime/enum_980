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
$oldTag = [Environment]::GetEnvironmentVariable('MICROPY_GIT_TAG', 'Process')
$oldHash = [Environment]::GetEnvironmentVariable('MICROPY_GIT_HASH', 'Process')
try {
    foreach ($flavor in @('stock', 'compat')) {
        $projectPath = Join-Path $reviewRoot "build/$flavor-130-core/ports/windows/micropython.vcxproj"
        $propsPath = Join-Path $reviewRoot 'config/stock-130.props'
        $env:MICROPY_GIT_TAG = 'v1.30.0-preview.9a3a0c0d5e'
        $env:MICROPY_GIT_HASH = '9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01'
        if ($flavor -eq 'compat') {
            $propsPath = Join-Path $reviewRoot 'config/compat.props'
            $env:MICROPY_GIT_TAG += '-enum980-review'
            $env:MICROPY_GIT_HASH += '+patched'
        }
        $logPath = Join-Path $reviewRoot "results/runtime-130-$flavor-build.log"
        & $MSBuild $projectPath /m /p:Configuration=Release /p:Platform=Win32 /p:PlatformToolset=v145 "/p:CustomPropsFile=$propsPath" "/p:PyPython=$Python" /verbosity:minimal *> $logPath
        $buildExit = $LASTEXITCODE
        Get-Content $logPath -Tail 12
        if ($buildExit -ne 0) { exit $buildExit }
    }
} finally {
    [Environment]::SetEnvironmentVariable('MICROPY_GIT_TAG', $oldTag, 'Process')
    [Environment]::SetEnvironmentVariable('MICROPY_GIT_HASH', $oldHash, 'Process')
}
