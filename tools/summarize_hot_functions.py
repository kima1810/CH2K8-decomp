"""Summarize interleaved hot-function timings; no gameplay FPS claim implied."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def summarize(path, start=0, end=float('inf')):
    totals = defaultdict(lambda: {'calls': 0, 'work_units': 0, 'wall_ns': 0})
    with Path(path).open(encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream):
            if not start <= float(row['elapsed_ms'])/1000 < end:
                continue
            total = totals[(row['function'], row['optimized'])]
            for key in total:
                total[key] += int(row[key])
    result = {}
    for (address, fast), total in sorted(totals.items()):
        total['ns_per_call'] = total['wall_ns']/total['calls'] if total['calls'] else None
        total['ns_per_work_unit'] = total['wall_ns']/total['work_units'] if total['work_units'] else None
        result.setdefault(address, {})['optimized' if fast == '1' else 'baseline'] = total
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=float('inf'))
    args = parser.parse_args()
    print(json.dumps(summarize(args.csv, args.start, args.end), indent=2))
