"""Add optional, paired-testable pack fast paths to three measured hot routines.

Only recognizes the complete already-corrected type-6 emission; never rewrites
other instructions or hand-edits generated sources. Generated duplicates stay
local. Unknown generator shapes fail rather than silently losing coverage.
"""
import re
from pathlib import Path

TARGETS = ('84723778', '84723CC0', '84724930')
MARKER = '// CH2K8 measured packed-vector variants'


def scalar_pack(dst, src, half):
    lines = [f'\t// vpkd3d128 {dst},{src},6,2,{half*2}', '\tvTemp.u64[0] = 0;']
    for component, lane in enumerate((3, 2, 1, 0)):
        minimum = '0x40380001u' if component < 3 else '0x40400000u'
        maximum = '0x4047FFFFu' if component < 3 else '0x4040000Fu'
        mask = '0xFFFFFu' if component < 3 else '0xFu'
        lines += [f'\ttemp.u32 = ctx.{src}.u32[{lane}];',
                  f'\tvTemp.u32[2] = {minimum};',
                  '\tif (!(temp.f32 >= vTemp.f32[2])) temp.u32 = vTemp.u32[2];',
                  f'\tvTemp.u32[2] = {maximum};',
                  '\tif (temp.f32 > vTemp.f32[2]) temp.u32 = vTemp.u32[2];',
                  f'\tvTemp.u64[0] |= uint64_t(temp.u32 & {mask}) << {component*20};']
    lines.append(f'\tctx.{dst}.u64[{half}] = vTemp.u64[0];')
    return '\n'.join(lines)


def optimize_source(text):
    if MARKER in text:
        return text, 0
    total = 0
    for index, address in enumerate(TARGETS):
        signature = f'DEFINE_REX_FUNC(sub_{address}) {{'
        if signature not in text:
            continue
        start = text.index(signature)
        end = text.index('\n}\n', start) + 3
        body = text[start:end]
        optimized = body
        sites = re.findall(r'\t// vpkd3d128 (v\d+),(v\d+),6,2,([02])\n', body)
        if len(sites) != 16:
            raise ValueError(f'{address}: expected 16 verified pack sites, got {len(sites)}')
        for dst, src, shift in sites:
            half = int(shift)//2
            original = scalar_pack(dst, src, half)
            if optimized.count(original) != 1:
                raise ValueError(f'{address}: unexpected pack shape {dst}/{src}/{half}')
            replacement = (f'\t// vpkd3d128 {dst},{src},6,2,{shift} (integer SIMD)\n'
                           f'\tCh2k8PackBiased64(ctx.{dst}, ctx.{src}, temp, vTemp, {half});')
            optimized = optimized.replace(original, replacement, 1)
        optimized = optimized.replace(signature,
            f'static void sub_{address}_fast(PPCContext& __restrict ctx, uint8_t* base) {{\n'
            f'\tCh2k8HotScope hot({index}, ctx.r3.u32, base, true);', 1)
        baseline = body.replace(signature, signature + '\n'
            f'\tif (Ch2k8SelectFastVectorPack({index})) {{\n'
            f'\t\tsub_{address}_fast(ctx, base);\n\t\treturn;\n\t}}\n'
            f'\tCh2k8HotScope hot({index}, ctx.r3.u32, base, false);', 1)
        text = text[:start] + optimized + '\n' + baseline + text[end:]
        total += len(sites)
    if total:
        text = MARKER + '\n#include "packed_vector_optimized.h"\n' + text
    return text, total


def optimize_directory(generated: Path):
    total = 0
    for path in sorted(generated.glob('*_recomp.*.cpp')):
        text = path.read_text(encoding='utf-8')
        if not any(f'DEFINE_REX_FUNC(sub_{a}) {{' in text for a in TARGETS):
            continue
        changed, count = optimize_source(text)
        if count:
            path.write_text(changed, encoding='utf-8', newline='\n')
            total += count
    return total
