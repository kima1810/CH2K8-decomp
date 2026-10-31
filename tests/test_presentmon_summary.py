import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from summarize_presentmon import summarize


def test_summary_separates_swap_chains_and_ignores_unavailable_gpu_values(tmp_path):
    capture = tmp_path / 'capture.csv'
    capture.write_text('\ufeffApplication,ProcessID,SwapChainAddress,TimeInMs,MsBetweenPresents,MsGPUBusy\n'
                       'game,12,A,1000,16,NA\n'
                       'game,12,A,1016,16,2\n'
                       'game,12,B,1020,4,nan\n'
                       'game,12,A,1032,16,4\n', encoding='utf-8')
    result = summarize(capture, 1.01, 1.04)
    assert len(result) == 2
    chain_a = next(x for x in result if x['swap_chain'] == 'A')
    assert chain_a['rows'] == 2
    assert abs(chain_a['host_presents_per_second'] - 62.5) < 0.0001
    assert chain_a['metrics_ms']['MsGPUBusy']['mean'] == 3
    chain_b = next(x for x in result if x['swap_chain'] == 'B')
    assert 'MsGPUBusy' not in chain_b['metrics_ms']
    assert chain_b['host_presents_per_second'] is None


def test_profiling_blocker_dispatch_has_all_original_targets():
    from audit_inline_switches import read_emitted
    generated = Path(__file__).resolve().parents[1] / 'port/generated/default'
    if not generated.is_dir():
        import pytest
        pytest.skip('Requires local generated code')
    tables = {}
    for path in generated.glob('*_recomp.*.cpp'):
        tables.update(read_emitted(path.read_text()))
    assert tables[0x84C1EBB0] == {
        'register': 11, 'function': 'sub_84C1EAA8',
        'labels': [0x84C1EC30, 0x84C1ED5C, 0x84C1ED5C, 0x84C1EDCC, 0x84C1EDF4,
                   0x84C1EF9C, 0x84C1EFC0, 0x84C1F028, 0x84C1EFE4, 0x84C1F028, 0x84C1F028],
    }
