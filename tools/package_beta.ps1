<# Build a portable beta ZIP from existing compiled output. No game data is included. #>
[CmdletBinding()]
param([string]$BuildDirectory, [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
# A caller using PowerShell 7 may pass a module path without Windows modules.
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Utility')
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Archive')
$repo = Split-Path -Parent $PSScriptRoot
if (-not $BuildDirectory) { $BuildDirectory = Join-Path $repo 'port/out/build/win-amd64-vulkan' }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $repo 'out/beta' }
$runtime = @('ch2k8.exe', 'rexruntime.dll', 'rexgpu-xenos.dll', 'ch2k8_asset_codec.dll')
foreach ($name in $runtime) {
    if (-not (Test-Path -LiteralPath (Join-Path $BuildDirectory $name) -PathType Leaf)) { throw "Build file missing: $name" }
}
$stage = Join-Path $OutputDirectory ('ZMO-beta1-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss-ffff'))
$null = New-Item -ItemType Directory -Path (Join-Path $stage 'tools') -Force
foreach ($name in $runtime) { Copy-Item -LiteralPath (Join-Path $BuildDirectory $name) -Destination $stage }
foreach ($name in @('launch_ch2k8.ps1', 'launcher_import.py', 'loose_assets.py', 'ch2k8_archive.py', 'xbox_texture.py', 'xdvdfs.py',
    'xbox_disc_source.py', 'direct_folder.py', 'materialize_paired.py', 'prepare_direct_assets.py', 'xbox_asset_edits.py')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $stage 'tools')
}
Copy-Item -LiteralPath (Join-Path $repo 'Launch CH2K8.cmd') -Destination $stage
Copy-Item -LiteralPath (Join-Path $repo 'BETA.md') -Destination (Join-Path $stage 'START HERE.md')
Copy-Item -LiteralPath (Join-Path $repo 'port/third_party/XENIA_TEXTURE_LICENSE.txt') -Destination $stage
$licenses = Join-Path $repo 'port/sdk-vulkan/licenses'
if (Test-Path -LiteralPath $licenses) { Copy-Item -LiteralPath $licenses -Destination (Join-Path $stage 'licenses') -Recurse }
$revision = & git -C $repo rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot identify source revision.' }
@{version='ZMO-beta1';source_revision=$revision;built_utc=[DateTime]::UtcNow.ToString('o');game_data_included=$false} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stage 'beta-version.json') -Encoding UTF8
Get-ChildItem -LiteralPath $stage -File -Recurse | ForEach-Object {
    (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() + '  ' + $_.FullName.Substring($stage.Length + 1)
} | Set-Content -LiteralPath (Join-Path $stage 'SHA256SUMS.txt') -Encoding ASCII
$zip = $stage + '.zip'
Compress-Archive -LiteralPath $stage -DestinationPath $zip -CompressionLevel Optimal
Write-Output "Beta package: $zip"
