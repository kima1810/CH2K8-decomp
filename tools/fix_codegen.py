"""Correct the pinned ReXGlue SDK's vupkd3d128 20-bit sign extension.

The SDK emits a 32-bit cast followed by a 44-bit right shift. Widening that
cast preserves the shifted 64-bit value until after arithmetic sign extension.
Only the three exact emitted expressions are eligible. No game bytes are read.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


BROKEN_SIGN_EXTENSION = re.compile(
    r"(\b\w+\.s32 = \()int32_t(\(\w+\.u64\[0\] << (?:44|24|4)\) >> 44\);)"
)


def correct_sign_extension(source: str) -> tuple[str, int]:
    return BROKEN_SIGN_EXTENSION.subn(r"\1int64_t\2", source)


def correct_directory(generated: Path) -> tuple[int, int]:
    sources = sorted(generated.glob("*_recomp.*.cpp"))
    if not sources:
        raise ValueError(f"No recompiled sources found in {generated}")
    total = 0
    changed = 0
    for path in sources:
        original = path.read_bytes()
        corrected, count = correct_sign_extension(original.decode("utf-8"))
        if count:
            path.write_bytes(corrected.encode("utf-8"))
            total += count
            changed += 1
    return total, changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generated", type=Path, help="Generated default/ directory")
    parser.add_argument("--stamp", type=Path, help="Touch when corrected output changes")
    args = parser.parse_args()
    total, changed = correct_directory(args.generated)
    print(f"vupkd3d128: corrected {total} expressions in {changed} files")
    if args.stamp and (total or not args.stamp.exists()):
        args.stamp.parent.mkdir(parents=True, exist_ok=True)
        args.stamp.touch()


if __name__ == "__main__":
    main()
