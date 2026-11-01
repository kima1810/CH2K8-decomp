"""Checked per-draw ROV shader specialization for the pinned source SDK."""
from pathlib import Path
import subprocess
from prepare_native_gpu_sdk import replace_once

ROOT = Path(__file__).resolve().parents[1]


def patch_header(text):
    text = replace_once(text, '#pragma once', '#pragma once\n#include <rex/graphics/native_pixel_state.h>\n#include <rex/graphics/pipeline/render_target/cache.h>')
    text = replace_once(text, 'kVersion = 0x20260226;', 'kVersion = 0x20261103;')
    text = replace_once(text, '      DepthStencilMode depth_stencil_mode : 2;',
                        '      DepthStencilMode depth_stencil_mode : 2;\n'
                        '      uint32_t native_pixel_state : 16;')
    signature = '  dxbc::Src LoadSystemConstant(SystemConstants::Index index, size_t offset, uint32_t swizzle) {\n'
    text = replace_once(text, signature, signature+'''    // CH2K8 exact-state shader specialization v3
    if (current_shader().type() == xenos::ShaderType::kPixel && edram_rov_used_) {
      const auto state = GetDxbcShaderModification().pixel.native_pixel_state;
      if (ch2k8::PixelStateEnabled(state) && swizzle == dxbc::Src::kXXXX) {
        if (index == SystemConstants::Index::kEdramRTFormatFlags &&
            offset == offsetof(SystemConstants, edram_rt_format_flags)) {
          return dxbc::Src::LU(RenderTargetCache::AddPSIColorFormatFlags(
              xenos::ColorRenderTargetFormat(ch2k8::ColorFormat(state))));
        }
        if (index == SystemConstants::Index::kEdramRTBlendFactorsOps &&
            offset == offsetof(SystemConstants, edram_rt_blend_factors_ops) &&
            ch2k8::HasBlend(state)) return dxbc::Src::LU(ch2k8::BlendControl(state));
      }
    }
    if (current_shader().type() == xenos::ShaderType::kPixel && edram_rov_used_ &&
        index == SystemConstants::Index::kSampleCountLog2 &&
        offset == offsetof(SystemConstants, sample_count_log2)) {
      const auto state = GetDxbcShaderModification().pixel.native_pixel_state;
      if (ch2k8::CanFoldSamples(state, swizzle)) {
        return dxbc::Src::LU(ch2k8::SampleLog2(state, swizzle & 3),
            ch2k8::SampleLog2(state, (swizzle >> 2) & 3),
            ch2k8::SampleLog2(state, (swizzle >> 4) & 3),
            ch2k8::SampleLog2(state, (swizzle >> 6) & 3));
      }
    }
''')
    before = '  dxbc::Src LoadFlagsSystemConstant() {\n'
    text = replace_once(text, before, '''  dxbc::Src LoadMaskedFlagsSystemConstant(uint32_t mask) {
    if (current_shader().type() == xenos::ShaderType::kPixel && edram_rov_used_) {
      const auto state = GetDxbcShaderModification().pixel.native_pixel_state;
      if (ch2k8::CanFoldFlags(state, mask)) return dxbc::Src::LU(ch2k8::PixelFlags(state));
    }
    return LoadFlagsSystemConstant();
  }
'''+before)
    return text


def patch_pipeline(text):
    text = replace_once(text, 'REXCVAR_DEFINE_BOOL(d3d12_dxbc_disasm,', '''REXCVAR_DEFINE_BOOL(ch2k8_native_pixel_state, true, "GPU/CH2K8",
                    "Specialize exact ROV sample, format, alpha and common blend state")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

REXCVAR_DEFINE_BOOL(d3d12_dxbc_disasm,''')
    start = text.index('DxbcShaderTranslator::Modification PipelineCache::GetCurrentPixelShaderModification(')
    end = text.index('\n}\n', start)
    part = text[start:end]
    part = replace_once(part, '  return modification;', '''  // CH2K8 exact-state shader specialization v3
  if (REXCVAR_GET(ch2k8_native_pixel_state) &&
      render_target_cache_.GetPath() == RenderTargetCache::Path::kPixelShaderInterlock) {
    static_assert(DxbcShaderTranslator::kSysFlag_DepthFloat24_Shift == 6);
    static_assert(DxbcShaderTranslator::kSysFlag_AlphaPassIfLess_Shift == 7);
    static_assert(uint32_t(xenos::BlendOp::kMin) == 2);
    static_assert(uint32_t(xenos::BlendFactor::kSrcAlpha) == 6);
    const auto color = regs.Get<reg::RB_COLORCONTROL>();
    uint32_t flags = uint32_t(regs.Get<reg::RB_DEPTH_INFO>().depth_format ==
        xenos::DepthRenderTargetFormat::kD24FS8) << 6;
    flags |= uint32_t(color.alpha_test_enable ? color.alpha_func :
        xenos::CompareFunction::kAlways) << 7;
    const auto rt0 = regs.Get<reg::RB_COLOR_INFO>(reg::RB_COLOR_INFO::rt_register_indices[0]);
    modification.pixel.native_pixel_state = ch2k8::PackPixelState(
        uint32_t(regs.Get<reg::RB_SURFACE_INFO>().msaa_samples), flags,
        uint32_t(rt0.color_format),
        regs[reg::RB_BLENDCONTROL::rt_register_indices[0]] & 0x1FFF1FFFu);
  }
  return modification;''')
    return text[:start]+part+text[end:]


def patch_output(text):
    # Each replaced operand is immediately masked to precisely these bits.
    text = replace_once(text, 'LoadFlagsSystemConstant(),\n               dxbc::Src::LU(kSysFlag_ConvertColor0ToGamma << i)',
                        'LoadMaskedFlagsSystemConstant(kSysFlag_ConvertColor0ToGamma << i),\n               dxbc::Src::LU(kSysFlag_ConvertColor0ToGamma << i)')
    for prefix in ('dxbc::Dest::R(system_temp_depth_stencil_, 0b0010)',
                   'dxbc::Dest::R(temp_temp, 1 << temp_temp_component)'):
        text = replace_once(text, prefix+', LoadFlagsSystemConstant(),',
                            prefix+', LoadMaskedFlagsSystemConstant(kSysFlag_DepthFloat24),')
    text = replace_once(text, 'dxbc::Src::LU(kSysFlag_AlphaPassIfLess_Shift),\n              LoadFlagsSystemConstant());',
                        'dxbc::Src::LU(kSysFlag_AlphaPassIfLess_Shift),\n              LoadMaskedFlagsSystemConstant(7u << kSysFlag_AlphaPassIfLess_Shift));')
    return text


def prepare_native_shaders(source):
    functions = {
        'include/rex/graphics/pipeline/shader/dxbc_translator.h': patch_header,
        'src/graphics/d3d12/pipeline_cache.cpp': patch_pipeline,
        'src/graphics/pipeline/shader/dxbc_translator_om.cpp': patch_output,
    }
    changes = {}
    for relative, patch in functions.items():
        original = subprocess.check_output(['git', '-C', str(source), 'show', 'HEAD:'+relative], text=True)
        expected = patch(original)
        path = source/relative
        if path.read_text() not in (original, expected):
            raise ValueError('Unreviewed shader SDK changes: '+relative)
        changes[path] = expected
    for path, expected in changes.items():
        if path.read_text() != expected:
            path.write_text(expected, encoding='utf-8', newline='\n')
    destination = source/'include/rex/graphics/native_pixel_state.h'
    data = (ROOT/'port/sdk_patches/native_pixel_state.h').read_bytes()
    if not destination.exists() or destination.read_bytes() != data:
        destination.write_bytes(data)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    prepare_native_shaders(parser.parse_args().source)
