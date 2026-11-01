<#
.SYNOPSIS
Build the pinned Windows SDK with native Vulkan and D3D12 in an isolated prefix.
#>
[CmdletBinding()]
param([ValidateRange(1, 16)][int]$Jobs = 3)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot 'work/third_party/rexglue-vulkan'
$build = Join-Path $repoRoot 'port/out/build/sdk-vulkan'
$install = Join-Path $repoRoot 'port/sdk-vulkan'
$pin = 'bd833a2ab69d305f99ddf57418fc38ffec8af93d'
function Check-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed with exit code $LASTEXITCODE" }
}
if (-not (Test-Path -LiteralPath $source)) {
    git clone --depth 50 --branch nightly-20261002-bd833a2a https://github.com/rexglue/rexglue-sdk.git $source
    Check-Exit 'SDK clone'
}
$revision = git -C $source rev-parse HEAD
Check-Exit 'SDK revision check'
if ($revision -ne $pin) { throw "Expected SDK $pin; found $revision. Use the pinned source in $source." }
git -C $source submodule update --init --depth 1 --jobs $Jobs
Check-Exit 'SDK dependencies'
$description = $null
try { $description = git -C $source describe --tags --long --match 'v[0-9]*.[0-9]*' --exclude '*-*' 2>$null } catch { }
if (-not $description) {
    git -C $source fetch --deepen=50 origin tag nightly-20261002-bd833a2a
    Check-Exit 'SDK version ancestry'
}
python (Join-Path $PSScriptRoot 'prepare_vulkan_sdk.py') $source
Check-Exit 'SDK preparation'
cmake -S $source -B $build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DREXGLUE_USE_VULKAN=ON -DREXGLUE_USE_D3D12=ON -DREXGLUE_BUILD_TESTS=OFF -DCMAKE_EXPORT_NO_PACKAGE_REGISTRY=ON "-DCMAKE_INSTALL_PREFIX=$install"
Check-Exit 'SDK configure'
cmake --build $build --parallel $Jobs
Check-Exit 'SDK build'
cmake --install $build --config Release
Check-Exit 'SDK install'
Push-Location (Join-Path $repoRoot 'port')
try {
    cmake --preset win-amd64-vulkan
    Check-Exit 'Game configure'
    cmake --build --preset win-amd64-vulkan --parallel $Jobs
    Check-Exit 'Game build'
} finally { Pop-Location }
