"""Report backend experiments without treating guest submissions as display FPS."""
import argparse
import csv
import json
import statistics
from pathlib import Path

from summarize_guest_frames import summarize


def read_csv(path):
    if not path.is_file():
        return []
    with path.open(encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def summarize_run(root, start=120, end=180):
    root = Path(root)
    metadata = json.loads((root/'run.json').read_text(encoding='utf-8-sig'))
    result = {'profile': metadata.get('profile'),
              'executable_sha256': metadata.get('executable_sha256'),
              'runtime_binaries_sha256': metadata.get('runtime_binaries_sha256'),
              'matched_scene': False, 'window_seconds': [start, end],
              'stopped_at_limit': metadata.get('stopped_at_limit'),
              'exit_code': metadata.get('exit_code')}
    frames = root/'guest-frames.csv'
    result['guest_submissions'] = summarize(frames, start, end) if frames.is_file() else None
    process = [r for r in read_csv(root/'process.csv') if start <= float(r['elapsed_s']) < end]
    if len(process) >= 2:
        elapsed = float(process[-1]['elapsed_s'])-float(process[0]['elapsed_s'])
        result['mean_process_cpu_cores'] = ((float(process[-1]['cpu_time_s'])-float(process[0]['cpu_time_s']))/elapsed) if elapsed > 0 else None
        result['peak_sampled_working_set_bytes'] = max(int(r['working_set_bytes']) for r in process)
    sensors = [r for r in read_csv(root/'amd.csv') if start <= float(r['second']) < end]
    result['amd_raw_sensor_medians'] = {}
    for key in ('gfx_clock_raw', 'mem_clock_raw', 'gfx_activity_raw', 'edge_temp_raw',
                'hotspot_temp_raw', 'asic_power_raw', 'throttler_raw'):
        values = [float(r[key]) for r in sensors if r.get(key) not in (None, '', 'NA')]
        result['amd_raw_sensor_medians'][key] = statistics.median(values) if values else None
    log_path = root/'runtime.log'
    log = log_path.read_text(encoding='utf-8-sig', errors='replace') if log_path.is_file() else ''
    result['pipeline_creation_log_entries'] = log.count('Creating graphics pipeline state')
    result['placeholder_presentation_skip_entries'] = log.count('Skipping Vulkan frame presentation')
    result['native_readbacks'] = sorted(p.name for p in root.glob('output-*.bmp'))
    result['limits'] = ('Autonomous demo scenes are not locked; guest submission rate is not unique displayed FPS. '
                        'Pipeline log counts are not creation durations. Sensor values retain tool raw units; '
                        'unsupported sensors are null. Native readbacks require visual inspection.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--start', type=float, default=120)
    parser.add_argument('--end', type=float, default=180)
    args = parser.parse_args()
    if args.start < 0 or args.end <= args.start:
        parser.error('Require 0 <= start < end')
    print(json.dumps(summarize_run(args.run, args.start, args.end), indent=2))
