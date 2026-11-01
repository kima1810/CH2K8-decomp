import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from prove_vector_store_ranges import prove_store_span, transfer, TOP
from optimize_codegen import restore_source
import pytest


def body(expression):
    return '\n'.join([
        '\tctx.r11.u64 = REX_LOAD_U32(ctx.r3.u32 + 116);',
        '\tctx.r4.u64 = REX_LOAD_U16(ctx.r3.u32);',
        '\tctx.r4.u64 = ctx.r4.u64 & 0xFFC;',
        expression,
        '\t// stvlx v1,r11,r4',
        '\tea = ctx.r11.u32 + ctx.r4.u32;',
        '\treturn;',
    ])


def test_mask_shift_bound_and_alignment():
    proof = prove_store_span(body('\tctx.r4.u64 = __builtin_rotateleft64(ctx.r4.u32 | (ctx.r4.u64 << 32), 3) & 0x7FFFFFFF8;'))
    assert proof == {'span': 32752, 'maximum_offset': 32736, 'sites': 1}


def test_unknown_values_calls_and_base_mutation_fail_closed():
    assert prove_store_span(body('\tctx.r4.u64 = unknown;')) is None
    assert prove_store_span(body('\thelper(ctx, base);')) is None
    assert prove_store_span(body('\tctx.r11.u64 = 0;')) is None
    assert prove_store_span(body('\tctx.r4.u8 = 1;')) is None
    assert prove_store_span(body('\tctx.r11.u64 += 4;')) is None
    assert prove_store_span(body('\tctx.r11.u64 |= 4;')) is None
    assert prove_store_span(body('\tctx.r4.u64 |= 4;')) is None
    assert prove_store_span(body('\t++ctx.r4.u64;')) is None
    assert prove_store_span(body('\tfor (;;) ctx.r4.u64 += 4;')) is None


def test_backedge_cannot_assume_observed_loop_count():
    loop = 'loc_1234:\n\tctx.r4.u64 = ctx.r4.u64 + 4;\n\tif (condition) goto loc_1234;'
    assert prove_store_span(body(loop)) is None


def test_scalar_transfer_never_assumes_high_bits_of_partial_write():
    state = [(TOP, 0)] * 32
    assert transfer('ctx.r4.u32 = 0;', state)[4][0] == TOP
    assert transfer('ctx.r4.u64 = REX_LOAD_U16(0);', state)[4] == (65535, 0)


def test_local_generated_routines_have_only_two_proven_spans():
    root = Path(__file__).resolve().parents[1] / 'port/generated/default'
    found = {}
    for path in root.glob('*_recomp.*.cpp'):
        text = path.read_text()
        for address in ('84723778', '84723CC0', '84724930'):
            signature = f'DEFINE_REX_FUNC(sub_{address}) {{'
            if signature not in text:
                continue
            original = restore_source(text)
            start = original.index(signature)
            end = original.index('\n}\n', start)
            found[address] = prove_store_span(original[start:end])
    if not found:
        pytest.skip('Requires local generated sources')
    assert found == {
        '84723778': {'span': 40960, 'maximum_offset': 40944, 'sites': 16},
        '84723CC0': {'span': 40960, 'maximum_offset': 40944, 'sites': 16},
        '84724930': None,
    }
