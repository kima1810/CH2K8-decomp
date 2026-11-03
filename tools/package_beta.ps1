<# Build a portable beta ZIP from existing compiled output. No game data is included. #>
[CmdletBinding()]
param([string]$BuildDirectory, [string]$OutputDirectory, [string]$PythonDirectory, [string]$CrtDirectory)
$ErrorActionPreference = 'Stop'
# A caller using PowerShell 7 may pass a module path without Windows modules.
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Utility')
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Archive')
$repo = Split-Path -Parent $PSScriptRoot
if (-not $BuildDirectory) { $BuildDirectory = Join-Path $repo 'port/out/build/win-amd64-vulkan' }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $repo 'out/beta' }
if (-not $PythonDirectory) { $PythonDirectory = Join-Path $repo 'out/beta-deps/python' }
if (-not $CrtDirectory) { $CrtDirectory = Join-Path $repo 'out/beta-deps/crt' }
foreach ($name in @('python.exe', 'python314.dll', 'python314.zip', 'LICENSE.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $PythonDirectory $name) -PathType Leaf)) { throw "Bundled Python missing: $name. Run tools/prepare_beta_deps.ps1 first." }
}
$crtFiles = @('msvcp140.dll', 'msvcp140_atomic_wait.dll', 'vcruntime140.dll', 'vcruntime140_1.dll')
foreach ($name in $crtFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $CrtDirectory $name) -PathType Leaf)) { throw "C++ runtime missing: $name. Run tools/prepare_beta_deps.ps1 first." }
}
$controllerRoot = Join-Path $repo 'out/beta-deps'
foreach ($name in @('gamecontrollerdb.txt', 'CONTROLLER_LICENSE.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $controllerRoot $name) -PathType Leaf)) { throw 'Controller mappings missing. Run tools/prepare_beta_deps.ps1.' }
}
$runtime = @('ch2k8.exe', 'rexruntime.dll', 'rexgpu-xenos.dll', 'ch2k8_asset_codec.dll')
foreach ($name in $runtime) {
    if (-not (Test-Path -LiteralPath (Join-Path $BuildDirectory $name) -PathType Leaf)) { throw "Build file missing: $name" }
}
$stage = Join-Path $OutputDirectory ('ZMO-beta1-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-ffff'))
$null = New-Item -ItemType Directory -Path (Join-Path $stage 'tools') -Force
Copy-Item -LiteralPath (Join-Path $controllerRoot 'gamecontrollerdb.txt') -Destination $stage
Copy-Item -LiteralPath (Join-Path $controllerRoot 'CONTROLLER_LICENSE.txt') -Destination $stage
Copy-Item -LiteralPath $PythonDirectory -Destination (Join-Path $stage 'python') -Recurse
# Isolate Python from registry, PATH, user packages and PYTHONPATH.
'python314.zip', '.', '../tools' | Set-Content -LiteralPath (Join-Path $stage 'python/python314._pth') -Encoding ASCII
foreach ($name in $crtFiles) {
    Copy-Item -LiteralPath (Join-Path $CrtDirectory $name) -Destination $stage
    Copy-Item -LiteralPath (Join-Path $CrtDirectory $name) -Destination (Join-Path $stage 'python') -Force
}
foreach ($name in $runtime) { Copy-Item -LiteralPath (Join-Path $BuildDirectory $name) -Destination $stage }
foreach ($name in @('verify_beta.py', 'launch_ch2k8.ps1', 'start_launcher.ps1', 'beta_diagnostics.ps1', 'launcher_import.py', 'loose_assets.py', 'ch2k8_archive.py', 'xbox_texture.py', 'xdvdfs.py',
    'xbox_disc_source.py', 'direct_folder.py', 'materialize_paired.py', 'prepare_direct_assets.py', 'xbox_asset_edits.py')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $stage 'tools')
}
Copy-Item -LiteralPath (Join-Path $repo 'Launch CH2K8.cmd') -Destination $stage
Copy-Item -LiteralPath (Join-Path $repo 'BETA_TESTING.md') -Destination $stage
Copy-Item -LiteralPath (Join-Path $repo 'BETA.md') -Destination (Join-Path $stage 'START HERE.md')
Copy-Item -LiteralPath (Join-Path $repo 'port/third_party/XENIA_TEXTURE_LICENSE.txt') -Destination $stage
$licenses = Join-Path $repo 'port/sdk-vulkan/licenses'
if (Test-Path -LiteralPath $licenses) { Copy-Item -LiteralPath $licenses -Destination (Join-Path $stage 'licenses') -Recurse }
$sdkSource = Join-Path $repo 'work/third_party/rexglue-vulkan'
if (Test-Path -LiteralPath (Join-Path $sdkSource 'LICENSE')) {
    $null = New-Item -ItemType Directory -Path (Join-Path $stage 'licenses/rexglue') -Force
    Copy-Item -LiteralPath (Join-Path $sdkSource 'LICENSE') -Destination (Join-Path $stage 'licenses/rexglue/LICENSE')
    # Preserve third-party copyright and license notices alongside the runtime.
    Get-ChildItem -LiteralPath (Join-Path $sdkSource 'thirdparty') -File -Recurse | Where-Object { $_.Name -match '^(LICENSE|COPYING|NOTICE)([._-].*)?$' } | ForEach-Object {
        $relative = $_.FullName.Substring($sdkSource.Length + 1)
        $destination = Join-Path (Join-Path $stage 'licenses/rexglue') $relative
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force
        Copy-Item -LiteralPath $_.FullName -Destination $destination
    }
}
$revision = & git -C $repo rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot identify source revision.' }
$buildHashes = @{}
foreach ($name in $runtime) { $buildHashes[$name] = (Get-FileHash -LiteralPath (Join-Path $stage $name) -Algorithm SHA256).Hash.ToLowerInvariant() }
$dirty = [bool](& git -C $repo status --porcelain --untracked-files=normal)
@{version='ZMO-beta1';source_revision=$revision;built_utc=[DateTime]::UtcNow.ToString('o');game_data_included=$false;python='3.14.10';platform='windows-x64';cpu_minimum='SSE4.1';build_files=$buildHashes;source_dirty=$dirty;controller_db_revision='07af1d50187e94c861c9f9f5d8a55b148f11306b'} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stage 'beta-version.json') -Encoding UTF8
Get-ChildItem -LiteralPath $stage -File -Recurse | ForEach-Object {
    (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() + '  ' + $_.FullName.Substring($stage.Length + 1)
} | Set-Content -LiteralPath (Join-Path $stage 'SHA256SUMS.txt') -Encoding ASCII
# Reject incomplete x64 DLL dependency closures before creating a distributable.
& (Join-Path $stage 'python/python.exe') (Join-Path $stage 'tools/verify_beta.py') $stage | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Beta binary/inventory verification failed. No ZIP was created.' }
$zip = $stage + '.zip'
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($stage, $zip, [IO.Compression.CompressionLevel]::Optimal, $true)
Write-Output "Beta package: $zip"
