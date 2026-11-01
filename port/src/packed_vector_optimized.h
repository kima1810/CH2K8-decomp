#pragma once
#include <rex/ppc.h>
#include <simde/x86/sse4.1.h>

// [CONFIRMED] Bit-equivalent to the corrected type-6 biased-float pack.
// Integer comparisons avoid changing the host FP exception/rounding state.
inline void Ch2k8PackBiased64(PPCVRegister &destination,
                              const PPCVRegister &source,
                              PPCRegister &temporary, PPCVRegister &scratch,
                              unsigned half) {
  auto value = simde_mm_shuffle_epi32(
      simde_mm_load_si128(reinterpret_cast<const simde__m128i *>(source.u32)),
      SIMDE_MM_SHUFFLE(0, 1, 2, 3));
  const auto minimum =
      simde_mm_set_epi32(0x40400000, 0x40380001, 0x40380001, 0x40380001);
  const auto maximum =
      simde_mm_set_epi32(0x4040000F, 0x4047FFFF, 0x4047FFFF, 0x4047FFFF);
  // Negative bit patterns clamp to minimum under signed comparison. Positive
  // NaNs must also select minimum, while positive infinity clamps to maximum.
  auto nan = simde_mm_cmpgt_epi32(value, simde_mm_set1_epi32(0x7F800000));
  auto clamped =
      simde_mm_min_epi32(simde_mm_max_epi32(value, minimum), maximum);
  clamped = simde_mm_blendv_epi8(clamped, minimum, nan);
  const uint64_t xy = uint64_t(simde_mm_cvtsi128_si64(clamped));
  const uint64_t zw =
      uint64_t(simde_mm_cvtsi128_si64(simde_mm_srli_si128(clamped, 8)));
  scratch.u64[0] = (xy & 0xFFFFF) | (((xy >> 32) & 0xFFFFF) << 20) |
                   ((zw & 0xFFFFF) << 40) | (((zw >> 32) & 0xF) << 60);
  scratch.u32[2] = 0x4040000F;
  temporary.u32 = uint32_t(zw >> 32);
  destination.u64[half] = scratch.u64[0];
}

// Selected once per guest function call, never per vector instruction.
bool Ch2k8SelectFastVectorPack(unsigned index);
class Ch2k8HotScope {
public:
  Ch2k8HotScope(unsigned index, uint32_t descriptor, uint8_t *base, bool fast);
  ~Ch2k8HotScope();

private:
  uint64_t started_ = 0;
  uint32_t units_ = 0;
  unsigned index_ = 0;
  bool fast_ = false;
};
