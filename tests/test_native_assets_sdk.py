import subprocess
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from prepare_native_assets_sdk import prepare_native_assets


def test_pinned_native_asset_patch_is_complete_and_idempotent(tmp_path):
    source=ROOT/'work/third_party/rexglue-vulkan'
    if not (source/'.git').exists():pytest.skip('Requires local pinned source SDK')
    files=['include/rex/graphics/shared_memory.h','include/rex/graphics/d3d12/texture_cache.h',
           'src/graphics/d3d12/texture_cache.cpp','src/filesystem/devices/host_path_device.cpp']
    for name in files:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name]))
    prepare_native_assets(tmp_path)
    before={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    prepare_native_assets(tmp_path)
    assert before=={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert b'TryLoadNativeDDS' in before[Path(files[2])]
    assert b'NativeRangeWrittenByGpu' in before[Path(files[0])]
    assert b'native_revision' in before[Path(files[1])]
    assert b'native_retired_resources_' in before[Path(files[1])]
