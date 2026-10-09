# 2026-10-09: Phase 0 inventory and USRDIR archive

## Question
What is on the CH2K8 PS3 disc and the NBA 2K9 PC install? Which formats do they share, and what prior art already exists?

## Method
- Listed and extracted both reference archives into `work/` with Windows' built-in `tar.exe` (bsdtar 3.8.8, which reads 7z and RAR). `ref/` was not modified.
- Cloned [CHoops-Extractor-Reborn](https://github.com/ZMO34/CHoops-Extractor-Reborn) (commit `52e9bef`) to `work/third_party/` and read its docs and archive reader (not executed).
- Wrote an independent split-archive reader, `tools/ch2k8_archive.py`, with a header/TOC round-trip, and a loose-file cataloger, `tools/inventory.py`.
- Resolved TOC name hashes using the pattern namespace, the extractor's `names.json` (only CRC-reproducible pairs), the NBA 2K9 filenames, and a generated `shoe_###_##` family.
- Compared magic bytes for every filename present in both games.

## Evidence
- `USRDIR` holds only `EBOOT.BIN` (an `SCE\0` SELF) and the split archive `0A`..`0E` (magic `AA00B3BF`, 5 parts, 3,376 entries, alignment 0x800).
- Re-serializing the header, part table and TOC gives **byte-identical** output (54,120 bytes). `pytest tests/` passes 3 tests.
- TOC +0x0C is an **exact byte size**: for all 3,376 entries, `gap − 0x800 < size ≤ gap`. The prior-art tool reads it as 0x800 units and calls the sizes "impossible".
- TOC entries are sorted by hash ascending. Data offsets are unordered.
- 3,301 of 3,376 names resolve. 300 NBA 2K9 filenames hash-match CH2K8 entries.
- Of those 300 shared files, the 279 standard IFFs, 6 CDF-backed IFFs and `loc.iff` are exact byte-swapped magics on PC. The 6 H7A-headed `.cdf` files keep the same bytes. The 8 speech `.bin` banks differ entirely.
- 2K9 `cached_logos.cdf` H7A header parses sensibly only as BE (logical 240, stored 106, shift 12).
- CDF audio banks: `00000001 00000005 0000000F <u32> 0000BB80` (0xBB80 = 48000).

## Conclusion
- The CH2K8 asset layer is one hash-indexed archive of 2K IFF containers. It is the same IFF family as NBA 2K9 PC with endianness flipped, which makes 2K9 a strong reference for Phase 1. Details are in [file_inventory.md](file_inventory.md) and [usrdir_archive.md](../formats/usrdir_archive.md).
- CHoops-Extractor-Reborn already covers much of Phase 1: IFF, CDF, H7A, TXTR/GTF, SCNE and ROST, with bounded same-size writers. Phase 1 should verify and extend it rather than start from scratch, but its TOC size reading is wrong.

## Confidence
- Archive layout, byte sizes, IFF/CDF byte-swap relationship: [CONFIRMED].
- Name hash = CRC32(uppercase name): [LIKELY]. It reproduces 3,301 names, but the hash function hasn't been seen in code.
- H7A being BE on PC: [LIKELY] (one file checked).
- `E4791207` is a "set/list" format: [GUESS], based on the 2K9 filenames `*_set.iff`, `bootup.iff`, `loc.iff`.
- Speech `.bin` banks being audio in a PS3-specific codec: [GUESS], from the names and the repeating `0x924924` bit patterns.

## Open questions
- What are the 75 unresolved names? About 880 MB of them are `Axxxxxxx` speech-like banks. Candidates could come from EBOOT strings once it's decrypted.
- Which codec do the speech `.bin` banks use (ATRAC3? MSF? 2K custom)? Compare with the 2K9 PC `.bin` (`80808080`, which looks like 8-bit PCM or a PC codec).
- Does the game binary-search the TOC, and does it honor +0x0C or the padded extent? This can be checked in Phase 2 or with RPCS3.
- Can entries grow or move? This is the key question for modding, since the prior art only allows same-size patches. It needs a full archive rebuild plus an RPCS3 boot test.
