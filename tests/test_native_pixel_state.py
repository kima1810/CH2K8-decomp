import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from prepare_native_shader_sdk import patch_header, patch_pipeline, patch_output, prepare_native_shaders
from summarize_shader_comparison import summarize


def test_exact_state_keys_and_fold_masks(tmp_path):
    compiler = shutil.which('clang++')
    if not compiler:
        pytest.skip('Requires C++ compiler')
    source = tmp_path/'state.cpp'
    source.write_text(r'''
#include "native_pixel_state.h"
#include <set>
#include <cstdio>
using namespace rex::graphics::ch2k8;
int main() {
 std::set<unsigned> keys,full_keys;
 unsigned checks=0;
 for(unsigned samples=0;samples<4;++samples) for(unsigned flags=0;flags<16;++flags) {
  auto state=PackPixelState(samples,flags<<6);
  if(state>=65536 || !keys.insert(state).second || !PixelStateEnabled(state)) return 1;
  if(PixelFlags(state)!=(flags<<6)) return 2;
  if(SampleLog2(state,0)!=unsigned(samples>=2) || SampleLog2(state,1)!=unsigned(samples>=1)) return 3;
  for(unsigned mask=0;mask<16;++mask) {
   if(!CanFoldFlags(state,mask<<6) || (PixelFlags(state)&(mask<<6)) != ((flags<<6)&(mask<<6))) return 4;
   if(CanFoldFlags(state,(mask<<6)|(1<<14)) || CanFoldFlags(0,mask<<6)) return 5;
   ++checks;
  }
  for(unsigned swizzle=0;swizzle<256;++swizzle)
   if(CanFoldSamples(state,swizzle) != ((swizzle&0xAA)==0)) return 6;
  for(unsigned format=0;format<16;++format) for(unsigned index=0;index<32;++index) {
   unsigned blend=0xFFFFFFFFu;
   if(index) {auto h=kBlendHalves[index-1];blend=h|(h<<16);}
   auto full=PackPixelState(samples,flags<<6,format,blend);
   if(ColorFormat(full)!=format || HasBlend(full)!=bool(index) ||
      (index && BlendControl(full)!=blend) ||
      PixelFlags(full)!=(flags<<6) || !PixelStateEnabled(full)) return 7;
   if(!full_keys.insert(full).second) return 8;
  }
 }
 if(full_keys.size()!=32768) return 9;
 printf("%u exact state/mask comparisons; 32768 unique full keys\n",checks);
}
''')
    exe = tmp_path/'state.exe'
    build = subprocess.run([compiler,'-std=c++17','-O2','-I',str(ROOT/'port/sdk_patches'),str(source),'-o',str(exe)],capture_output=True,text=True)
    assert build.returncode == 0, build.stderr
    result = subprocess.run([str(exe)],capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    assert '1024 exact state/mask comparisons' in result.stdout


def test_pinned_shader_patches_and_atomic_rejection(tmp_path, monkeypatch):
    upstream = ROOT/'work/third_party/rexglue-vulkan'
    if not upstream.is_dir():
        pytest.skip('Requires local pinned SDK')
    functions = {
        'include/rex/graphics/pipeline/shader/dxbc_translator.h': patch_header,
        'src/graphics/d3d12/pipeline_cache.cpp': patch_pipeline,
        'src/graphics/pipeline/shader/dxbc_translator_om.cpp': patch_output,
    }
    originals = {}
    for name, patch in functions.items():
        original = subprocess.check_output(['git','-C',str(upstream),'show','HEAD:'+name],text=True)
        originals[name] = original
        path = tmp_path/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(original)
        assert patch(original) != original
    monkeypatch.setattr(subprocess,'check_output',lambda args,**kw: originals[args[-1].removeprefix('HEAD:')])
    prepare_native_shaders(tmp_path)
    before = {name:(tmp_path/name).read_bytes() for name in functions}
    prepare_native_shaders(tmp_path)
    assert all((tmp_path/name).read_bytes()==value for name,value in before.items())
    changed = tmp_path/'src/graphics/pipeline/shader/dxbc_translator_om.cpp'
    changed.write_text(changed.read_text()+'\n// unrelated local modification\n')
    before = {p:p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    with pytest.raises(ValueError,match='Unreviewed shader'):
        prepare_native_shaders(tmp_path)
    assert all(p.read_bytes()==value for p,value in before.items())


@pytest.mark.parametrize('state,flag',[('baseline','--no-ch2k8_native_pixel_state'),('optimized','--ch2k8_native_pixel_state')])
def test_bounded_capture_configuration(tmp_path,state,flag):
    shell=shutil.which('powershell.exe')
    if not shell:pytest.skip('Requires PowerShell')
    disc=tmp_path/'disc with spaces';disc.mkdir();(disc/'default.xex').touch()
    exe=tmp_path/'unused exe.exe';exe.touch()
    command=[shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/capture_gpu_workload.ps1'),'-ValidateOnly',
             '-Executable',str(exe),'-RenderDoc',str(exe),'-GameData',str(disc),'-ShaderState',state]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    config=json.loads(result.stdout)
    assert flag in config['arguments'] and '--render_target_path_d3d12=rov' in config['arguments']
    assert config['duration_seconds']==200 and not config['matched_scene']
    assert not Path(config['run_root']).exists()
    bad=subprocess.run(command+['-DurationSeconds','130'],capture_output=True,text=True)
    assert bad.returncode != 0 and 'exceed capture delay' in bad.stderr


def test_paired_counter_summary_requires_matching_warmed_trials(tmp_path):
    path=tmp_path/'paired.tsv'
    rows=['trial\tvariant\tevent\tms']
    for trial in (1,2,3):
        for name,values in [('original',(3,7)),('specialized',(2,6))]:
            for event,value in zip((10,20),values):
                rows.append(f'{trial}\t{name}\t{event}\t{value}')
    path.write_text('\n'.join(rows)+'\n')
    result=summarize(path,10)
    assert result['median_sum_reduction']==pytest.approx(.2)
    assert result['median_target_reduction']==pytest.approx(1/3)
    assert 'not displayed FPS' in result['limits']
    path.write_text('\n'.join(rows[:-1])+'\n')
    with pytest.raises(ValueError,match='Mismatched'):
        summarize(path,10)
