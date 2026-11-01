<#
.SYNOPSIS
CH2K8 launcher: choose renderer, resolution, refresh rate and window mode.
#>
[CmdletBinding()]
param(
    [ValidateSet('d3d12', 'vulkan')][string]$Renderer = 'd3d12',
    [ValidateSet('auto', 'native', 'accurate')][string]$RenderPath = 'auto',
    [ValidateSet('1280x720', '1600x900', '1920x1080', '2560x1440', '3840x2160')]
    [string]$Resolution = '1280x720',
    [ValidateRange(24, 240)][int]$RefreshRate = 60,
    [ValidateSet('windowed', 'borderless', 'exclusive')][string]$WindowMode = 'windowed',
    [string]$GameData,
    [string]$Executable,
    [string]$PreviewOutput,
    [switch]$Launch,
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$settingsPath = Join-Path $repoRoot 'port/userdata/launcher.json'
if (-not $GameData) { $GameData = Join-Path $repoRoot 'work/ch2k8/XBOX/disc' }

function Get-LaunchConfiguration {
    param([string]$Backend, [string]$Size, [int]$Hertz, [string]$Mode, [string]$Data, [string]$Program, [string]$Path = 'auto')
    if ($Backend -notin @('d3d12', 'vulkan')) { throw 'Choose a supported renderer.' }
    if ($Path -notin @('auto', 'native', 'accurate')) { throw 'Choose a supported rendering mode.' }
    if ($Size -notmatch '^(1280x720|1600x900|1920x1080|2560x1440|3840x2160)$') {
        throw 'Choose a supported resolution.'
    }
    if ($Hertz -lt 24 -or $Hertz -gt 240) { throw 'Refresh rate must be between 24 and 240 Hz.' }
    if ($Mode -notin @('windowed', 'borderless', 'exclusive')) { throw 'Choose a window mode.' }
    if (-not $Program) {
        $dualBuild = Join-Path $repoRoot 'port/out/build/win-amd64-vulkan/ch2k8.exe'
        $preset = if ($Backend -eq 'vulkan' -or (Test-Path -LiteralPath $dualBuild)) { 'win-amd64-vulkan' } else { 'win-amd64' }
        $Program = Join-Path $repoRoot "port/out/build/$preset/ch2k8.exe"
    }
    if (-not (Test-Path -LiteralPath $Program -PathType Leaf)) {
        throw "Game build is missing: $Program. See port/README.md for build instructions."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Data 'default.xex') -PathType Leaf)) {
        throw 'Choose the extracted Xbox 360 game folder containing default.xex.'
    }
    $Program = (Resolve-Path -LiteralPath $Program).Path
    $Data = (Resolve-Path -LiteralPath $Data).Path
    $userData = Join-Path $repoRoot 'port/userdata'
    $arguments = @('--gpu_plugin=xenos', "--ch2k8_renderer=$Backend",
        "--game_data_root=$Data", "--user_data_root=$userData",
        "--resolution=$Size", "--video_mode_refresh_rate=$Hertz")
    if ($Mode -eq 'windowed') { $arguments += @('--no-fullscreen', '--no-fullscreen_exclusive') }
    elseif ($Mode -eq 'exclusive') { $arguments += @('--fullscreen', '--fullscreen_exclusive') }
    else { $arguments += @('--fullscreen', '--no-fullscreen_exclusive') }
    if ($Backend -eq 'd3d12') {
        $target = if ($Path -eq 'native') { 'rtv' } else { 'rov' }
        $arguments += "--render_target_path_d3d12=$target"
    } else {
        $target = if ($Path -eq 'native') { 'fbo' } else { 'fsi' }
        $arguments += "--render_target_path_vulkan=$target"
    }
    # Start-Process joins arguments into a command line. Paths may contain spaces;
    # quote each complete argument and reject embedded native quote characters.
    foreach ($argument in $arguments) {
        if ($argument.Contains('"')) { throw 'Paths must not contain double quotes.' }
    }
    [pscustomobject]@{ executable = $Program; arguments = $arguments }
}

function Start-Ch2k8 {
    param($Configuration)
    if (Get-Process ch2k8 -ErrorAction SilentlyContinue) { throw 'CH2K8 is already running.' }
    $nativeArguments = $Configuration.arguments | ForEach-Object { '"' + $_ + '"' }
    Start-Process -FilePath $Configuration.executable -WorkingDirectory (Split-Path -Parent $Configuration.executable) -ArgumentList $nativeArguments -WindowStyle Normal -PassThru
}

if ($Launch -or $ValidateOnly) {
    $configuration = Get-LaunchConfiguration $Renderer $Resolution $RefreshRate $WindowMode $GameData $Executable $RenderPath
    if ($ValidateOnly) { $configuration | ConvertTo-Json -Depth 3 }
    else { Start-Ch2k8 $configuration | Select-Object Id }
    return
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
try {
    if (Test-Path -LiteralPath $settingsPath) {
        $saved = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
        if (-not $PSBoundParameters.ContainsKey('Renderer') -and $saved.renderer -in @('d3d12', 'vulkan')) { $Renderer = $saved.renderer }
        if (-not $PSBoundParameters.ContainsKey('RenderPath') -and $saved.render_path -in @('auto', 'native', 'accurate')) { $RenderPath = $saved.render_path }
        if (-not $PSBoundParameters.ContainsKey('Resolution') -and $saved.resolution -match '^(1280x720|1600x900|1920x1080|2560x1440|3840x2160)$') { $Resolution = $saved.resolution }
        if (-not $PSBoundParameters.ContainsKey('RefreshRate') -and $saved.refresh_rate -ge 24 -and $saved.refresh_rate -le 240) { $RefreshRate = [int]$saved.refresh_rate }
        if (-not $PSBoundParameters.ContainsKey('WindowMode') -and $saved.window_mode -in @('windowed', 'borderless', 'exclusive')) { $WindowMode = $saved.window_mode }
        if (-not $PSBoundParameters.ContainsKey('GameData') -and $saved.game_data) { $GameData = [string]$saved.game_data }
    }
} catch { Write-Verbose "Ignoring invalid launcher settings: $_" }

$form = New-Object System.Windows.Forms.Form
$form.Text = 'College Hoops 2K8'
$form.ClientSize = New-Object System.Drawing.Size(620, 514)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)
$form.BackColor = [System.Drawing.Color]::FromArgb(24, 28, 35)
$form.ForeColor = [System.Drawing.Color]::WhiteSmoke
$form.AutoScaleMode = 'Dpi'

function Add-Label([string]$Text, [int]$X, [int]$Y, [int]$Width = 260) {
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Text
    $label.Location = New-Object System.Drawing.Point($X, $Y)
    $label.Size = New-Object System.Drawing.Size($Width, 24)
    $form.Controls.Add($label)
    return $label
}
function Add-Choice([string[]]$Items, [int]$X, [int]$Y, [int]$Width = 260) {
    $choice = New-Object System.Windows.Forms.ComboBox
    $choice.DropDownStyle = 'DropDownList'
    $choice.Location = New-Object System.Drawing.Point($X, $Y)
    $choice.Size = New-Object System.Drawing.Size($Width, 30)
    $choice.Items.AddRange([object[]]$Items)
    $form.Controls.Add($choice)
    return $choice
}
$title = Add-Label 'COLLEGE HOOPS 2K8' 24 20 560
$title.Font = New-Object System.Drawing.Font('Segoe UI', 19, [System.Drawing.FontStyle]::Bold)
$title.Height = 40
$null = Add-Label 'Renderer' 24 80
$backend = Add-Choice @('Direct3D 12', 'Vulkan (experimental)') 24 106
$backend.SelectedIndex = if ($Renderer -eq 'vulkan') { 1 } else { 0 }
$null = Add-Label 'Window mode' 326 80
$mode = Add-Choice @('Windowed', 'Borderless fullscreen', 'Exclusive fullscreen') 326 106
$mode.SelectedIndex = @('windowed', 'borderless', 'exclusive').IndexOf($WindowMode)
$null = Add-Label 'Resolution' 24 155
$size = Add-Choice @('1280x720', '1600x900', '1920x1080', '2560x1440', '3840x2160') 24 181
$size.SelectedItem = $Resolution
$null = Add-Label 'Refresh rate (Hz)' 326 155
$rate = New-Object System.Windows.Forms.NumericUpDown
$rate.Minimum = 24; $rate.Maximum = 240; $rate.Value = $RefreshRate
$rate.Location = New-Object System.Drawing.Point(326, 181)
$rate.Size = New-Object System.Drawing.Size(260, 30)
$form.Controls.Add($rate)
$null = Add-Label 'Rendering mode' 24 229 560
$renderMode = Add-Choice @('Automatic', 'Native render targets', 'Accurate Xbox blending') 24 255 562
$renderMode.SelectedIndex = @('auto', 'native', 'accurate').IndexOf($RenderPath)
$hint = Add-Label 'Native targets are experimental and may flash black. Automatic uses accurate blending. 60 Hz retains original timing.' 24 296 570
$hint.ForeColor = [System.Drawing.Color]::Silver
$hint.Height = 40
$null = Add-Label 'Extracted game folder' 24 344 560
$dataBox = New-Object System.Windows.Forms.TextBox
$dataBox.Text = $GameData
$dataBox.Location = New-Object System.Drawing.Point(24, 370)
$dataBox.Size = New-Object System.Drawing.Size(466, 30)
$form.Controls.Add($dataBox)
$browse = New-Object System.Windows.Forms.Button
$browse.Text = 'Browse...'
$browse.Location = New-Object System.Drawing.Point(500, 368)
$browse.Size = New-Object System.Drawing.Size(86, 32)
$form.Controls.Add($browse)
$browse.Add_Click({
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = 'Select the extracted Xbox 360 disc folder containing default.xex'
    $dialog.SelectedPath = $dataBox.Text
    if ($dialog.ShowDialog($form) -eq 'OK') { $dataBox.Text = $dialog.SelectedPath }
    $dialog.Dispose()
})
$play = New-Object System.Windows.Forms.Button
$play.Text = 'Launch game'
$play.Location = New-Object System.Drawing.Point(392, 438)
$play.Size = New-Object System.Drawing.Size(194, 46)
$play.FlatStyle = 'Flat'
$play.BackColor = [System.Drawing.Color]::FromArgb(164, 43, 49)
$form.Controls.Add($play)
$form.AcceptButton = $play
$play.Add_Click({
    try {
        $selectedBackend = @('d3d12', 'vulkan')[$backend.SelectedIndex]
        $selectedMode = @('windowed', 'borderless', 'exclusive')[$mode.SelectedIndex]
        $selectedPath = @('auto', 'native', 'accurate')[$renderMode.SelectedIndex]
        $configuration = Get-LaunchConfiguration $selectedBackend ([string]$size.SelectedItem) ([int]$rate.Value) $selectedMode $dataBox.Text $Executable $selectedPath
        $null = Start-Ch2k8 $configuration
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent $settingsPath) -Force
        @{ renderer = $selectedBackend; render_path = $selectedPath; resolution = [string]$size.SelectedItem;
           refresh_rate = [int]$rate.Value; window_mode = $selectedMode;
           game_data = $dataBox.Text } | ConvertTo-Json | Set-Content -LiteralPath $settingsPath -Encoding utf8
        $form.Close()
    } catch {
        [System.Windows.Forms.MessageBox]::Show($form, $_.Exception.Message, 'Unable to launch', 'OK', 'Error') | Out-Null
    }
})
if ($PreviewOutput) {
    $form.Show()
    [System.Windows.Forms.Application]::DoEvents()
    $form.Refresh()
    $bitmap = New-Object System.Drawing.Bitmap($form.Width, $form.Height)
    $form.DrawToBitmap($bitmap, (New-Object System.Drawing.Rectangle(0, 0, $form.Width, $form.Height)))
    $bitmap.Save([System.IO.Path]::GetFullPath($PreviewOutput), [System.Drawing.Imaging.ImageFormat]::Png)
    $bitmap.Dispose()
} else {
    $null = $form.ShowDialog()
}
$form.Dispose()
