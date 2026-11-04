<# Build the supported USA recompilation from default.xex, a disc folder or ISO. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Source,
    [string]$PythonExecutable,
    [string]$SdkDirectory,
    [string]$BuildDirectory,
    [ValidateRange(1,16)][int]$Jobs=2,
    [switch]$CodeOnly,
    [switch]$ValidateOnly,
    [string]$LogFile
)
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Utility')
. (Join-Path $PSScriptRoot 'build_support.ps1')
$repo = Split-Path -Parent $PSScriptRoot
$Source = (Resolve-Path -LiteralPath $Source).Path
$kind = if (Test-Path -LiteralPath $Source -PathType Container) { 'folder' } elseif ([IO.Path]::GetExtension($Source) -ieq '.iso') { 'iso' } elseif ([IO.Path]::GetExtension($Source) -ieq '.xex') { 'xex' } else { throw 'Select a College Hoops 2K8 USA Xbox 360 XEX, extracted disc folder or ISO.' }
$expected='71e8983d1cc009e485696aad19b5fa4b4661761870e2c8972717b932c1e4be36'
$xex = if ($kind -eq 'folder') { Join-Path $Source 'default.xex' } elseif ($kind -eq 'xex') { $Source } else { $null }
if ($xex -and (-not (Test-Path -LiteralPath $xex -PathType Leaf) -or (Get-FileHash -LiteralPath $xex -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected)) { throw 'Unsupported XEX. This recompilation requires the original USA College Hoops 2K8 default.xex.' }
$python = Find-BuildPython $PythonExecutable $repo
$pythonCMake=$python.Replace('\','/')
$cmake = Find-BuildCommand 'cmake.exe' @('C:/Program Files/CMake/bin/cmake.exe')
$clang = Find-BuildCommand 'clang++.exe' @('C:/Program Files/LLVM/bin/clang++.exe')
$ninja = Find-BuildCommand 'ninja.exe' @("$env:LOCALAPPDATA/Microsoft/WinGet/Packages/Ninja-build.Ninja_*/ninja.exe")
foreach ($tool in @($cmake,$clang,$ninja)) { $env:PATH=(Split-Path -Parent $tool)+';'+$env:PATH }
if (-not $SdkDirectory) { $SdkDirectory=Join-Path $repo 'port/sdk-vulkan' }
$SdkDirectory=$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SdkDirectory)
if (-not $BuildDirectory) { $BuildDirectory=Join-Path $repo 'port/out/build/win-amd64-vulkan' }
$BuildDirectory=$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildDirectory)
$plan=[pscustomobject]@{source=$Source;source_kind=$kind;python=$python;cmake=$cmake;clang=$clang;ninja=$ninja;sdk=$SdkDirectory;build_directory=$BuildDirectory;code_only=[bool]$CodeOnly;xex_alone_needs_assets_for_play=$true}
if ($ValidateOnly) { $plan | ConvertTo-Json; return }
$transcript=$false
try {
    if ($LogFile) { $null=New-Item -ItemType Directory -Path (Split-Path -Parent $LogFile) -Force; Start-Transcript -LiteralPath $LogFile | Out-Null; $transcript=$true }
    filter Write-BuildLine { Write-Host $_ }
    function Check-BuildExit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw "$Step failed ($LASTEXITCODE). See the build log." } }
    $native=Join-Path $repo 'out/native-tools/ch2k8_tools.exe'
    # Refresh this target even when an older beta already created the executable.
    & $cmake -S (Join-Path $repo 'tools/native_assets') -B (Join-Path $repo 'out/native-tools') -G Ninja "-DCMAKE_CXX_COMPILER=$clang" '-DCMAKE_BUILD_TYPE=Release' "-DCMAKE_MAKE_PROGRAM=$ninja" | Write-BuildLine
    Check-BuildExit 'Native tools configure'
    & $cmake --build (Join-Path $repo 'out/native-tools') --parallel $Jobs | Write-BuildLine
    Check-BuildExit 'Native tools build'
    $stagedXex=Join-Path $repo 'work/ch2k8/XBOX/disc/default.xex'
    $null=New-Item -ItemType Directory -Path (Split-Path -Parent $stagedXex) -Force
    if (Test-Path -LiteralPath $stagedXex) { if ((Get-FileHash -LiteralPath $stagedXex).Hash.ToLowerInvariant() -ne $expected) { throw 'Existing code-generation XEX differs. It was left untouched.' } }
    if ($kind -eq 'iso') {
        & $native extract-xex $Source $stagedXex
        Check-BuildExit 'ISO executable extraction'
    } elseif (-not (Test-Path -LiteralPath $stagedXex)) { Copy-Item -LiteralPath $xex -Destination $stagedXex }
    if (-not (Test-Path -LiteralPath (Join-Path $SdkDirectory 'bin/rexglue.exe'))) {
        if ($SdkDirectory -ne (Join-Path $repo 'port/sdk-vulkan')) { throw 'The selected SDK directory is missing bin/rexglue.exe.' }
        $git=Find-BuildCommand 'git.exe' @('C:/Program Files/Git/cmd/git.exe')
        $env:PATH=(Split-Path -Parent $git)+';'+$env:PATH
        & (Join-Path $PSScriptRoot 'build_vulkan_sdk.ps1') -Jobs $Jobs -PythonExecutable $python -SdkOnly
    }
    $generator=Join-Path $SdkDirectory 'bin/rexglue.exe'
    Push-Location (Join-Path $repo 'port')
    try {
        & $python (Join-Path $PSScriptRoot 'run_codegen.py') $generator (Join-Path $repo 'port/ch2k8_manifest.toml') (Join-Path $repo 'port/generated/default') | Write-BuildLine
        Check-BuildExit 'Recompilation code generation'
        & $cmake -S (Join-Path $repo 'port') -B $BuildDirectory -G Ninja "-DCMAKE_CXX_COMPILER=$clang" "-DCMAKE_MAKE_PROGRAM=$ninja" '-DCMAKE_BUILD_TYPE=Release' "-DCMAKE_PREFIX_PATH=$SdkDirectory" '-DCH2K8_REQUIRE_VULKAN=ON' "-DPython3_EXECUTABLE=$pythonCMake" | Write-BuildLine
        Check-BuildExit 'Recompilation configure'
        & $cmake --build $BuildDirectory --target ch2k8 ch2k8_tools --parallel $Jobs | Write-BuildLine
        Check-BuildExit 'Recompilation build'
    } finally { Pop-Location }
    $gameData=if ($kind -eq 'folder') {$Source} elseif ($kind -eq 'xex') {Split-Path -Parent $Source} else {$null}
    if ($kind -eq 'iso' -and -not $CodeOnly) {
        $parent=Join-Path $repo 'work/installed';$null=New-Item -ItemType Directory -Path $parent -Force
        $gameData=Join-Path $parent ([IO.Path]::GetFileNameWithoutExtension($Source)+'-assets')
        if (Test-Path -LiteralPath $gameData) {
            if (-not (Test-Path -LiteralPath (Join-Path $gameData 'assets.json')) -or (Get-FileHash -LiteralPath (Join-Path $gameData 'default.xex')).Hash.ToLowerInvariant() -ne $expected) { throw 'Existing ISO installation is incomplete or incompatible. It was left untouched.' }
            & $native prepare $gameData; Check-BuildExit 'Installed asset validation'
        } else { & $native import $Source $gameData; Check-BuildExit 'ISO asset import' }
    }
    $ready=[bool]($gameData -and ((Test-Path -LiteralPath (Join-Path $gameData '0A')) -or (Test-Path -LiteralPath (Join-Path $gameData 'assets.map'))))
    $result=@{executable=(Join-Path $BuildDirectory 'ch2k8.exe');game_data=$gameData;data_ready=$ready;source_kind=$kind;python=$python}
    $state=Join-Path $repo 'port/userdata';$null=New-Item -ItemType Directory -Path $state -Force
    $result|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $state 'build-result.json') -Encoding UTF8
    if ($gameData) { @{game_data=$gameData;renderer='d3d12';executable=$result.executable}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $state 'launcher.json') -Encoding UTF8 }
    $result|ConvertTo-Json
} finally { if ($transcript) { Stop-Transcript | Out-Null } }
