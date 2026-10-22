# 2026-10-22: Port target decision and full archive rebuild

## Question
1. Which executable should the native PC port recompile: PS3 or Xbox 360?
2. Can the PS3 USRDIR archive be rebuilt with entries that grow or move? The prior art only supports same-size patches.

## Method
- Compared the PS3 and 360 recompilation toolchains and existing ports from `ref/docs/links.md`. Checked `nba2k9.exe`: sections, the PDB path, and whether a SecuROM section is present.
- Checked the retail archive layout on the JB dump: the gap between the TOC and the first data, the padding bytes, and whether gap equals `align_up(size)`.
- Added `rebuild` to `tools/ch2k8_archive.py` (plan, stream, split across parts, read back). Covered it with synthetic tests: unmodified identity, growth with relocation, adding a part, the hash-name fallback, and rejecting unknown entries.
- Ran `rebuild --check` on the real dump, then wrote a real rebuild with `loading.iff` grown by 4 KiB to the scratchpad and compared every entry with the source.

## Evidence
- `nba2k9.exe` is unpacked x86, with an 8 MB `.text` section and no SecuROM section. It contains the PDB path `o:\vcout\nba_vcout\vcsports\us\bin\win32dx\nba\nba_clean_opt.exe.pdb`, but the PDB isn't on disc.
- Archive: data starts at `0xD800`, and `0xD368`..`0xD800` is all zero. All 3,376 entries are tightly packed, and padding is zero (checked on 400 entries, then implied by the full check).
- `rebuild --check` with no replacements was **IDENTICAL** over the whole 4.8 GB logical space (55 s).
- Growing `loading.iff` by 4,096 bytes moved 3,375 entries. All 3,375 read back with the same content, the TOC hash order was unchanged, `0E` grew from 0x3D6B0 to 0x3D6B2 units, and the read-back of the new archive was OK.
- `pytest tests/`: 8 passed.

## Conclusion
- **The code target is the Xbox 360 XEX** via XenonRecomp/ReXGlue. See [port_strategy.md](../port_strategy.md).
- The archive writer can now resize and relocate entries, and it reproduces the retail archive exactly. On the format side, modding is no longer limited to same-size patches.

## Confidence
- Rebuild is format-correct: [CONFIRMED] (byte-identical identity rebuild, full read-back after relocation).
- The game accepts relocated entries: unknown. It needs an RPCS3 boot test.
- Parts past `0E` are named `0F`…: [GUESS].

## Open questions
- RPCS3 boot test of a relocated archive. Does the game honor the new offsets and sizes?
- Does the game read the part descriptors, or open `0A`..`0E` by hardcoded names?
- What container does the 360 version use? This needs a 360 dump.
