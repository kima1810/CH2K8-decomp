"""Catalog a directory of loose game files: extension, size, magic bytes.

Writes a per-file CSV and prints a per-extension summary as a Markdown table.
Magic is reported as raw bytes (hex) so endianness is never assumed; the
summary also names magics known from docs/formats (BE and LE spellings).
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Raw on-disk byte sequences. LE spellings are the BE value byte-reversed.
KNOWN = {
    "FF3BEF94": "IFF standard (BE)",
    "94EF3BFF": "IFF standard (LE)",
    "F0985030": "IFF CDF-backed (BE)",
    "305098F0": "IFF CDF-backed (LE)",
    "0E4837C3": "H7A (BE)",
    "C337480E": "H7A (LE)",
    "326B546C": "2kTl",
    "AA00B3BF": "USRDIR archive (BE)",
    "89504E47": "PNG",
    "52494646": "RIFF",
    "4D5A9000": "PE/MZ",
    "44445320": "DDS",
    "7F454C46": "ELF",
    "53434500": "SCE/SELF",
    "00505346": "PARAM.SFO",
}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True, help="per-file CSV path")
    args = ap.parse_args(argv)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite {args.output}")

    by_ext: dict[str, list] = defaultdict(list)
    magic_by_ext: dict[str, Counter] = defaultdict(Counter)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "ext", "size", "magic"])
        for p in sorted(args.root.rglob("*")):
            if not p.is_file():
                continue
            with p.open("rb") as fh:
                magic = fh.read(4).hex().upper()
            ext = p.suffix.lower() or "(none)"
            size = p.stat().st_size
            w.writerow([p.relative_to(args.root).as_posix(), ext, size, magic])
            by_ext[ext].append(size)
            magic_by_ext[ext][magic] += 1

    print("| ext | count | total bytes | min | max | magics (count) |")
    print("|---|---:|---:|---:|---:|---|")
    for ext, sizes in sorted(by_ext.items(), key=lambda kv: -sum(kv[1])):
        mags = ", ".join(f"`{m}`{' ' + KNOWN[m] if m in KNOWN else ''} ({c})"
                         for m, c in magic_by_ext[ext].most_common(4))
        if len(magic_by_ext[ext]) > 4:
            mags += f", +{len(magic_by_ext[ext]) - 4} more"
        print(f"| {ext} | {len(sizes)} | {sum(sizes):,} | {min(sizes):,} | {max(sizes):,} | {mags} |")


if __name__ == "__main__":
    main()
