"""Exercise ISO extraction, cancellation and the shipped launcher without a game."""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from launcher_import import import_iso
from test_loose_assets import make_disc


def make_iso(tmp_path, base=0):
    disc=tmp_path/'source';archive,_=make_disc(disc)
    image=tmp_path/'my Xbox game.iso'
    # A two-node XDVDFS directory containing the original XEX and archive.
    directory=struct.pack('<HHIIBB',0,4,38,len(archive),0,2)+b'0A'
    directory+=struct.pack('<HHIIBB',0,0,36,12,0,11)+b'default.xex'
    with image.open('wb') as out:
        out.seek(base+32*2048)
        out.write(struct.pack('<20sII',b'MICROSOFT*XBOX*MEDIA',34,len(directory)))
        out.seek(base+34*2048);out.write(directory)
        out.seek(base+36*2048);out.write(b'XEX2 fixture')
        out.seek(base+38*2048);out.write(archive)
    return image


def test_iso_becomes_authoritative_loose_assets_without_modifying_source(tmp_path):
    image=make_iso(tmp_path)
    before=hashlib.sha256(image.read_bytes()).digest()
    output=tmp_path/'editable installation'
    progress=tmp_path/'progress.json'
    result=import_iso(image,output,progress)
    assert Path(result['game_data'])==output
    assert result['storage']=='loose-resources'
    manifest=json.loads((output/'assets.json').read_text())
    assert manifest['storage']=='loose-resources'
    assert (output/'default.xex').read_bytes()==b'XEX2 fixture'
    assert (output/'assets.map').is_file() and (output/'native_dds.index').is_file()
    assert (output/'assets').is_dir() and not (output/'0A').exists()
    assert not (output/'_archive').exists() and not list(output.rglob('*.stored'))
    assert not list(tmp_path.glob('.ch2k8-import-*'))
    assert 'Finalizing' in json.loads(progress.read_text())['message']
    assert hashlib.sha256(image.read_bytes()).digest()==before
    with pytest.raises(ValueError,match='already exists'):import_iso(image,output)
    assert (output/'default.xex').read_bytes()==b'XEX2 fixture'


def test_xgd2_partition_import_and_malformed_directory_rejection(tmp_path):
    from xbox_disc_source import XboxISO
    image=make_iso(tmp_path,0xFD90000)
    source=XboxISO(image)
    with (source/'default.xex').open() as member:assert member.read()==b'XEX2 fixture'
    with image.open('r+b') as out:
        # Point the right node at itself; parsing must fail before extraction.
        out.seek(0xFD90000+34*2048+16+2);out.write(struct.pack('<H',4))
    with pytest.raises(ValueError,match='directory tree'):import_iso(image,tmp_path/'bad output')
    assert not (tmp_path/'bad output').exists()
    assert not list(tmp_path.glob('.ch2k8-import-*'))


def test_cancel_and_failure_remove_only_owned_staging(tmp_path,monkeypatch):
    import loose_assets
    image=make_iso(tmp_path)
    output=tmp_path/'game'
    unrelated=tmp_path/'keep';unrelated.mkdir();(unrelated/'edits').write_text('keep')
    cancel=tmp_path/'cancel'
    def interrupted(source,stage,**kwargs):
        stage.mkdir();(stage/'partial').write_text('partial')
        cancel.write_text('cancel');kwargs['progress'](1,2)
    monkeypatch.setattr(loose_assets,'import_disc',interrupted)
    with pytest.raises(InterruptedError):import_iso(image,output,cancel_file=cancel)
    assert not output.exists() and not list(tmp_path.glob('.ch2k8-import-*'))
    assert (unrelated/'edits').read_text()=='keep'
    cancel.unlink()
    def failed(source,stage,**kwargs):
        stage.mkdir();raise OSError('disk full')
    monkeypatch.setattr(loose_assets,'import_disc',failed)
    with pytest.raises(OSError,match='disk full'):import_iso(image,output)
    assert not output.exists() and not list(tmp_path.glob('.ch2k8-import-*'))


def test_relocated_beta_imports_iso_through_real_powershell_launcher(tmp_path):
    import zipfile
    shell=shutil.which('powershell.exe')
    if not shell:pytest.skip('Requires Windows PowerShell')
    build=tmp_path/'build';build.mkdir()
    # The fixture has no compressed streams; omit the fake codec after checking
    # package contents so the real importer uses its standard-library fallback.
    for name in ('ch2k8.exe','rexruntime.dll','rexgpu-xenos.dll','ch2k8_asset_codec.dll'):
        (build/name).write_bytes(b'fixture')
    result=subprocess.run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/package_beta.ps1'),
        '-BuildDirectory',str(build),'-OutputDirectory',str(tmp_path/'packages')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    archive,=(tmp_path/'packages').glob('*.zip')
    with zipfile.ZipFile(archive) as bundle:bundle.extractall(tmp_path/'moved beta')
    install,=(tmp_path/'moved beta').iterdir()
    for name in ('xbox_disc_source.py','direct_folder.py','materialize_paired.py','prepare_direct_assets.py','xbox_asset_edits.py'):
        assert (install/'tools'/name).is_file()
    (install/'ch2k8_asset_codec.dll').unlink()
    environment=dict(os.environ,PATH=str(Path(sys.base_prefix))+os.pathsep+os.environ['PATH'])
    image=make_iso(tmp_path)
    destination=tmp_path/'new loose game'
    command=[shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(install/'tools/launch_ch2k8.ps1'),
        '-ImportIso',str(image),'-InstallDirectory',str(destination)]
    result=subprocess.run(command,capture_output=True,text=True,env=environment)
    assert result.returncode==0,result.stdout+result.stderr
    assert Path(json.loads(result.stdout)['game_data'])==destination
    assert json.loads((destination/'assets.json').read_text())['storage']=='loose-resources'
    validation=subprocess.run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(install/'tools/launch_ch2k8.ps1'),
        '-ValidateOnly','-GameData',str(destination)],capture_output=True,text=True)
    assert validation.returncode==0,validation.stderr
    assert f'--game_data_root={destination}' in json.loads(validation.stdout)['arguments']
    repeated=subprocess.run(command,capture_output=True,text=True,env=environment)
    assert repeated.returncode!=0 and 'never overwritten' in repeated.stderr
    # Exercise the real modal progress dialog and its timer-driven completion.
    wrapper=tmp_path/'interactive.ps1'
    wrapper.write_text('''param($Launcher, $Image, $Destination, $Disc, $Program)
$ErrorActionPreference = 'Stop'
. $Launcher -ValidateOnly -GameData $Disc -Executable $Program | Out-Null
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object System.Windows.Forms.Form
try { Import-Ch2k8Iso $Image $Destination -Interactive }
finally { $form.Dispose() }
''')
    interactive=tmp_path/'interactive loose game'
    result=subprocess.run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(wrapper),
        '-Launcher',str(install/'tools/launch_ch2k8.ps1'),'-Image',str(image),
        '-Destination',str(interactive),'-Disc',str(destination),'-Program',str(install/'ch2k8.exe')],
        capture_output=True,text=True,env=environment,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    assert (interactive/'assets.json').is_file()
