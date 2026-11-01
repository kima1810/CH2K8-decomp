#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <simde/x86/ssse3.h>

// [CONFIRMED] Compare guest big-endian words with the host register snapshot.
// Integer bits preserve NaN payloads and distinguish positive/negative zero.
inline bool Ch2k8ConstantWordsEqual(const uint32_t *host, const uint32_t *guest,
                                    size_t words) {
  size_t i = 0;
  const auto mask = simde_mm_set_epi8(12, 13, 14, 15, 8, 9, 10, 11,
                                     4, 5, 6, 7, 0, 1, 2, 3);
  for (; words - i >= 4; i += 4) {
    const auto expected = simde_mm_shuffle_epi8(
        simde_mm_loadu_si128(reinterpret_cast<const simde__m128i *>(guest + i)), mask);
    const auto current = simde_mm_loadu_si128(reinterpret_cast<const simde__m128i *>(host + i));
    if (simde_mm_movemask_epi8(simde_mm_cmpeq_epi32(expected, current)) != 0xFFFF)
      return false;
  }
  for (; i < words; ++i) {
    uint32_t value;
    std::memcpy(&value, reinterpret_cast<const uint8_t *>(guest) + i * 4, 4);
    if (host[i] != __builtin_bswap32(value)) return false;
  }
  return true;
}

inline bool Ch2k8RangeWithin(uint32_t start, uint32_t count, uint32_t first,
                             uint32_t last) {
  return count && start >= first && start <= last && count <= last - start + 1;
}

// The caller proves [first_word, first_word+words) is inside 512 float vectors.
inline void Ch2k8ChangedConstantVectors(const uint32_t *host, const uint32_t *guest,
                                        uint32_t first_word, uint32_t words,
                                        uint64_t (&changed)[8]) {
  for (uint32_t i = 0; i < words; ++i) {
    uint32_t value;
    std::memcpy(&value, reinterpret_cast<const uint8_t *>(guest) + i * 4, 4);
    if (host[i] != __builtin_bswap32(value)) {
      const uint32_t vector = (first_word + i) >> 2;
      changed[vector >> 6] |= uint64_t(1) << (vector & 63);
    }
  }
}

inline bool Ch2k8ChangedConstantsUsed(const uint64_t *usage, const uint64_t *changed,
                                      uint32_t first, uint32_t last) {
  for (uint32_t index = first; index <= last; ++index)
    if ((usage[index >> 6] & changed[index >> 6]) & (uint64_t(1) << (index & 63)))
      return true;
  return false;
}
