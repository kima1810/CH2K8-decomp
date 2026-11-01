#pragma once
#include <cstdint>
#include <array>

namespace rex::graphics::ch2k8 {
// [CONFIRMED] Exact per-draw values, carried in the shader translation key.
// No shader hash, observed scene, or assumed game-wide state is used.
constexpr uint32_t kPixelFlagMask = 0xFu << 6;
constexpr uint32_t BlendHalf(unsigned source, unsigned op, unsigned destination) {
  return source | (op << 5) | (destination << 8);
}
// Exact reversible palette: Add/Subtract/Min/Max/RevSubtract with zero/one
// factors, plus common additive factor pairs. Asymmetric or unfamiliar
// color/alpha combinations remain dynamic. Values match the Xenos register.
// Changing this palette or the key layout requires bumping Modification::kVersion.
constexpr std::array<uint32_t,31> kBlendHalves{
  BlendHalf(1,0,1), BlendHalf(1,1,1), BlendHalf(1,2,1), BlendHalf(1,3,1), BlendHalf(1,4,1),
  BlendHalf(1,0,0), BlendHalf(1,1,0), BlendHalf(1,2,0), BlendHalf(1,3,0), BlendHalf(1,4,0),
  BlendHalf(0,0,1), BlendHalf(0,1,1), BlendHalf(0,2,1), BlendHalf(0,3,1), BlendHalf(0,4,1),
  BlendHalf(0,0,0), BlendHalf(0,1,0), BlendHalf(0,2,0), BlendHalf(0,3,0), BlendHalf(0,4,0),
  BlendHalf(6,0,7), BlendHalf(1,0,7), BlendHalf(6,0,1), BlendHalf(4,0,0), BlendHalf(8,0,0),
  BlendHalf(0,0,4), BlendHalf(8,0,4), BlendHalf(10,0,11), BlendHalf(1,0,11),
  BlendHalf(14,0,15), BlendHalf(12,0,13)};
constexpr uint32_t BlendIndex(uint32_t control) {
  for(unsigned i=0;i<kBlendHalves.size();++i) {
    const auto half=kBlendHalves[i];
    if(control==(half|(half<<16))) return i+1;
  }
  return 0;
}
constexpr uint32_t PackPixelState(uint32_t samples, uint32_t flags,
                                  uint32_t format = 0, uint32_t blend = 0xFFFFFFFFu) {
  return 0x8000u | (samples & 3u) | (((flags >> 6) & 15u) << 2) |
         ((format & 15u) << 6) | (BlendIndex(blend) << 10);
}
constexpr bool PixelStateEnabled(uint32_t state) { return (state & 0x8000u) != 0; }
constexpr uint32_t PixelFlags(uint32_t state) { return ((state >> 2) & 15u) << 6; }
constexpr uint32_t ColorFormat(uint32_t state) { return (state >> 6) & 15u; }
constexpr bool HasBlend(uint32_t state) { return ((state >> 10) & 31u) != 0; }
constexpr uint32_t BlendControl(uint32_t state) {
  const unsigned index=(state >> 10) & 31u;
  if(!index) return 0;
  const auto half=kBlendHalves[index-1];
  return half|(half<<16);
}
constexpr uint32_t SampleLog2(uint32_t state, unsigned component) {
  const auto samples = state & 3u;
  return component ? unsigned(samples >= 1) : unsigned(samples >= 2);
}
constexpr bool CanFoldFlags(uint32_t state, uint32_t mask) {
  return PixelStateEnabled(state) && !(mask & ~kPixelFlagMask);
}
constexpr bool CanFoldSamples(uint32_t state, uint32_t swizzle) {
  return PixelStateEnabled(state) && !(swizzle & 0xAAu);
}
}  // namespace rex::graphics::ch2k8
