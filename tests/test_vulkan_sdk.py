import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import prepare_vulkan_sdk as sdk


def test_prepare_sdk_materializes_windows_links_and_forwards_refresh(tmp_path, monkeypatch):
    dependency = tmp_path/'thirdparty/libmspack'
    link = dependency/'cabextract/mspack/test.c'
    target = dependency/'libmspack/mspack/test.c'
    link.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    link.write_text('../../libmspack/mspack/test.c')
    target.write_text('int original_dependency_code;\n')
    window = tmp_path/'src/ui/window_sdl.cpp'
    window.parent.mkdir(parents=True)
    window.write_text('SDL_GetClosestFullscreenDisplayMode(display, width, height, 0.0f, true, &mode)')

    def git_output(args, **kwargs):
        if 'rev-parse' in args:
            return sdk.PIN
        if 'ls-files' in args:
            return '120000 test 0\tcabextract/mspack/test.c\n'
        if 'show' in args:
            return '../../libmspack/mspack/test.c'
        raise AssertionError(args)

    monkeypatch.setattr(sdk.subprocess, 'check_output', git_output)
    sdk.prepare(tmp_path)
    assert link.read_bytes() == target.read_bytes()
    assert 'float(REXCVAR_GET(video_mode_refresh_rate))' in window.read_text()
    expected = window.read_bytes()
    sdk.prepare(tmp_path)
    assert window.read_bytes() == expected
    assert target.read_text() == 'int original_dependency_code;\n'


def test_prepare_sdk_rejects_unreviewed_revision_before_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(sdk.subprocess, 'check_output', lambda *a, **k: 'different-commit')
    with pytest.raises(ValueError, match='Expected pinned SDK'):
        sdk.prepare(tmp_path)
    assert list(tmp_path.iterdir()) == []
