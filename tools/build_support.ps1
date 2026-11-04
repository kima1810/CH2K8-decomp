# Interpreter detection is used only by source compilation, never by the beta runtime.
function Find-BuildPython {
    param([string]$Explicit, [string]$RepoRoot)
    $candidates = New-Object 'System.Collections.Generic.List[object]'
    if ($Explicit) {
        $command = Get-Command $Explicit -ErrorAction SilentlyContinue
        $resolved = if (Test-Path -LiteralPath $Explicit -PathType Leaf) { (Resolve-Path -LiteralPath $Explicit).Path } elseif ($command) { $command.Source } else { $Explicit }
        $candidates.Add(@($resolved, @()))
    } else {
        $candidates.Add(@((Join-Path $RepoRoot 'port/out/python-env/Scripts/python.exe'), @()))
        $py = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($py) { $candidates.Add(@($py.Source, @('-3'))) }
        foreach ($command in @(Get-Command python.exe,python3.exe -All -ErrorAction SilentlyContinue)) { $candidates.Add(@($command.Source, @())) }
        foreach ($pattern in @('HKCU:/SOFTWARE/Python/PythonCore/*/InstallPath','HKLM:/SOFTWARE/Python/PythonCore/*/InstallPath')) {
            foreach ($key in @(Get-Item -Path $pattern -ErrorAction SilentlyContinue)) {
                $exe = $key.GetValue('ExecutablePath')
                if (-not $exe -and $key.GetValue('')) { $exe = Join-Path $key.GetValue('') 'python.exe' }
                if ($exe) { $candidates.Add(@($exe, @())) }
            }
        }
        foreach ($pattern in @("$env:LOCALAPPDATA/Programs/Python/Python*/python.exe",'C:/Python3*/python.exe')) {
            foreach ($file in @(Get-Item -Path $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)) { $candidates.Add(@($file.FullName, @())) }
        }
    }
    foreach ($candidate in $candidates) {
        $exe = [string]$candidate[0]
        if (-not $exe -or $exe -match '\\Microsoft\\WindowsApps\\' -or -not (Test-Path -LiteralPath $exe -PathType Leaf)) { continue }
        $process = $null
        try {
            $info = New-Object Diagnostics.ProcessStartInfo
            $info.FileName = $exe
            $info.Arguments = (@($candidate[1]) + @('-c', '"import sys,json; print(json.dumps(dict(executable=sys.executable,valid=sys.version_info>=(3,11))))"')) -join ' '
            $info.UseShellExecute = $false; $info.CreateNoWindow = $true
            $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
            $process = [Diagnostics.Process]::Start($info)
            $stdout = $process.StandardOutput.ReadToEndAsync(); $stderr = $process.StandardError.ReadToEndAsync()
            if (-not $process.WaitForExit(10000)) { $process.Kill(); $process.WaitForExit(); continue }
            if ($process.ExitCode -ne 0) { continue }
            $probe = $stdout.GetAwaiter().GetResult() | ConvertFrom-Json
            if ($probe.valid -and (Test-Path -LiteralPath $probe.executable -PathType Leaf)) { return [string]$probe.executable }
        } catch { }
        finally { if ($process) { $process.Dispose() } }
    }
    throw 'Source compilation needs Python 3.11+. A Windows Store execution alias is not an interpreter. Pass -PythonExecutable with the installed python.exe path, or install Python with the py launcher. The downloadable runnable beta does not need Python.'
}
function Find-BuildCommand {
    param([string]$Name, [string[]]$Candidates)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($pattern in $Candidates) {
        $file = Get-Item -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($file) { return $file.FullName }
    }
    throw "Source compilation needs $Name. Install the documented C++ build prerequisites or download the runnable beta ZIP."
}
