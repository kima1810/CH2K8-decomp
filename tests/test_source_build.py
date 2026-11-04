"""Source-checkout setup regressions from tester reports."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
SHELL=shutil.which('powershell.exe')
pytestmark=pytest.mark.skipif(not SHELL,reason='Windows PowerShell required')


def test_installed_python_is_resolved_to_real_executable(tmp_path):
    wrapper=tmp_path/'probe.ps1'
    wrapper.write_text('''param($Support,$Interpreter,$Root)
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Utility')
. $Support
Find-BuildPython -Explicit $Interpreter -RepoRoot $Root
''',encoding='utf-8')
    result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(wrapper),'-Support',str(ROOT/'tools/build_support.ps1'),'-Interpreter',sys.executable,'-Root',str(tmp_path)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert Path(result.stdout.strip()).is_file()
    assert 'WindowsApps' not in result.stdout


def test_store_alias_is_rejected_without_running_it(tmp_path):
    alias=tmp_path/'Microsoft/WindowsApps/python.exe';alias.parent.mkdir(parents=True);alias.write_bytes(b'not a real interpreter')
    wrapper=tmp_path/'alias.ps1'
    wrapper.write_text('''param($Support,$Alias,$Root)
$ErrorActionPreference='Stop'
. $Support
Find-BuildPython -Explicit $Alias -RepoRoot $Root
''',encoding='utf-8')
    result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(wrapper),'-Support',str(ROOT/'tools/build_support.ps1'),'-Alias',str(alias),'-Root',str(tmp_path)],capture_output=True,text=True)
    assert result.returncode!=0
    assert 'execution alias is not an interpreter' in result.stderr


def test_source_build_rejects_wrong_xex_before_building(tmp_path):
    xex=tmp_path/'default.xex';xex.write_bytes(b'wrong title')
    result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/build_ch2k8.ps1'),'-Source',str(xex),'-ValidateOnly'],capture_output=True,text=True)
    assert result.returncode!=0 and 'Unsupported XEX' in result.stderr


def test_native_xex_extraction_is_readonly_and_preserves_existing_file(tmp_path):
    tool=ROOT/'out/native-tools/ch2k8_tools.exe'
    if not tool.is_file():pytest.skip('Build native tools first')
    from test_launcher_import import make_iso
    image=make_iso(tmp_path);before=hashlib.sha256(image.read_bytes()).digest()
    output=tmp_path/'generated input/default.xex'
    command=[str(tool),'extract-xex',str(image),str(output),'--expected-xex-sha256',hashlib.sha256(b'XEX2 fixture').hexdigest()]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert output.read_bytes()==b'XEX2 fixture'
    assert json.loads(result.stdout)['xex']
    assert subprocess.run(command,capture_output=True).returncode==0
    output.write_bytes(b'keep existing edits')
    assert subprocess.run(command,capture_output=True).returncode!=0
    assert output.read_bytes()==b'keep existing edits'
    assert hashlib.sha256(image.read_bytes()).digest()==before


def test_launcher_build_validation_rejects_wrong_xex_without_starting_build(tmp_path):
    xex=tmp_path/'wrong.xex';xex.write_bytes(b'wrong title')
    result=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/launch_ch2k8.ps1'),'-BuildSource',str(xex),'-ValidateOnly'],capture_output=True,text=True)
    assert result.returncode!=0 and 'Unsupported XEX' in result.stderr


def test_native_import_handles_deep_derived_header_paths(tmp_path):
    tool=ROOT/'out/native-tools/ch2k8_tools.exe'
    if not tool.is_file():pytest.skip('Build native tools first')
    from test_loose_assets import make_disc
    source=tmp_path/'disc';make_disc(source)
    parent=tmp_path/('nested-installation-'+'a'*22)/('nested-installation-'+'b'*22)/('nested-installation-'+'c'*22)
    parent.mkdir(parents=True)
    output=parent/'game'
    result=subprocess.run([str(tool),'import',str(source),str(output),'--expected-xex-sha256',hashlib.sha256(b'XEX2 fixture').hexdigest()],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert (output/'assets.map').is_file()
    # The temporary import is deeper than its final destination; native metadata
    # writes must use Win32 extended paths without changing relative map entries.
    assert '_runtime/headers/' in (output/'assets.map').read_text()
    runtime=subprocess.run([str(tool),'validate-runtime',str(output)],capture_output=True,text=True)
    assert runtime.returncode==0,runtime.stderr
    assert not list(parent.glob('.ch2k8-import-*'))
