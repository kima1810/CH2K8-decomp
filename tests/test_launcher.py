"""Exercise the real PowerShell argument builder without opening a game or UI."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('backend,mode,flags', [
    ('d3d12', 'windowed', ['--no-fullscreen', '--render_target_path_d3d12=rtv', '--execute_unclipped_draw_vs_on_cpu', '--no-async_shader_compilation']),
    ('vulkan', 'exclusive', ['--fullscreen', '--fullscreen_exclusive', '--render_target_path_vulkan=fsi']),
    ('vulkan', 'borderless', ['--fullscreen', '--no-fullscreen_exclusive', '--render_target_path_vulkan=fsi']),
])
def test_launcher_builds_explicit_backend_and_display_args(tmp_path, backend, mode, flags):
    shell = shutil.which('powershell.exe')
    if not shell:
        pytest.skip('Requires Windows PowerShell')
    data = tmp_path / 'disc with spaces'
    data.mkdir()
    (data / 'default.xex').write_bytes(b'')
    executable = tmp_path / 'unused executable.exe'
    executable.write_bytes(b'')
    command = [shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
               str(ROOT/'tools/launch_ch2k8.ps1'), '-ValidateOnly',
               '-Renderer', backend, '-WindowMode', mode, '-Resolution', '1920x1080',
               '-RefreshRate', '120', '-GameData', str(data), '-Executable', str(executable)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    configuration = json.loads(result.stdout)
    arguments = configuration['arguments']
    assert f'--game_data_root={data}' in arguments
    assert f'--ch2k8_renderer={backend}' in arguments
    assert '--resolution=1920x1080' in arguments
    assert '--video_mode_refresh_rate=120' in arguments
    assert all(flag in arguments for flag in flags)
    if backend == 'vulkan':
        assert not any('render_target_path_d3d12' in arg for arg in arguments)
    # A missing disc must fail before launching or saving configuration.
    (data/'default.xex').unlink()
    failure = subprocess.run(command, capture_output=True, text=True)
    assert failure.returncode != 0
    assert 'default.xex' in failure.stderr


@pytest.mark.parametrize('backend,path,target', [
    ('d3d12', 'native', '--render_target_path_d3d12=rtv'),
    ('d3d12', 'accurate', '--render_target_path_d3d12=rov'),
    ('vulkan', 'native', '--render_target_path_vulkan=fbo'),
    ('vulkan', 'accurate', '--render_target_path_vulkan=fsi'),
])
def test_launcher_selects_native_or_accurate_targets(tmp_path, backend, path, target):
    shell = shutil.which('powershell.exe')
    if not shell:
        pytest.skip('Requires Windows PowerShell')
    data = tmp_path/'disc'
    data.mkdir()
    (data/'default.xex').write_bytes(b'')
    program = tmp_path/'game.exe'
    program.write_bytes(b'')
    result = subprocess.run([shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        str(ROOT/'tools/launch_ch2k8.ps1'), '-ValidateOnly', '-Renderer', backend,
        '-RenderPath', path, '-Executable', str(program), '-GameData', str(data)],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    arguments=json.loads(result.stdout)['arguments']
    assert target in arguments
    bounded='--execute_unclipped_draw_vs_on_cpu' in arguments
    synchronous='--no-async_shader_compilation' in arguments
    assert bounded == (backend=='d3d12' and path=='native')
    assert synchronous == bounded
