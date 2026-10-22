# CH2K8 PS3 USRDIR split archive (`0A`..`0E`)

Tool: [`tools/ch2k8_archive.py`](../../tools/ch2k8_archive.py) · Tests: [`tests/test_ch2k8_archive.py`](../../tests/test_ch2k8_archive.py)
Prior art: [ZMO34/CHoops-Extractor-Reborn](https://github.com/ZMO34/CHoops-Extractor-Reborn) `choops_py/archive/usrdir_reader.py` (disagrees on the TOC size field; see below).

All game data on the PS3 disc lives in one logical archive split across the files
`0A`, `0B`, `0C`, `0D`, `0E` in `PS3_GAME/USRDIR/`. The logical address space is the
concatenation of those parts in descriptor order; entries may straddle part boundaries.
The header, part table and TOC sit at the start of `0A`.

**Endianness: big-endian throughout** (part names are UTF-16BE).

## Header (0x18 bytes @ 0x00)

| Offset | Size | Type | Endian | Name | Confidence | Notes |
|---|---|---|---|---|---|---|
| 0x00 | 4 | u32 | BE | magic | [CONFIRMED] | `AA00B3BF` |
| 0x04 | 4 | u32 | BE | alignment | [LIKELY] | `0x800`; unit for TOC offsets and part sizes |
| 0x08 | 4 | u32 | BE | part_count | [CONFIRMED] | 5; matches files on disc |
| 0x0C | 4 | u32 | BE | reserved0 | [GUESS] | always 0 |
| 0x10 | 4 | u32 | BE | entry_count | [CONFIRMED] | 3376 (0xD30) |
| 0x14 | 4 | u32 | BE | reserved1 | [GUESS] | always 0 |

## Part descriptor (0x10 bytes × part_count @ 0x18)

| Offset | Size | Type | Endian | Name | Confidence | Notes |
|---|---|---|---|---|---|---|
| 0x00 | 4 | u32 | BE | size_units | [CONFIRMED] | × 0x800 = file size on disc, all 5 parts |
| 0x04 | 4 | u32 | BE | unknown | [GUESS] | always 0 |
| 0x08 | 8 | char16[4] | BE | name | [CONFIRMED] | UTF-16BE `"0A"` + NUL padding |

## TOC entry (0x10 bytes × entry_count, after part table)

| Offset | Size | Type | Endian | Name | Confidence | Notes |
|---|---|---|---|---|---|---|
| 0x00 | 4 | u32 | BE | name_hash | [LIKELY] | `CRC32(upper(ascii filename))`; 3301/3376 reproduced from candidate names |
| 0x04 | 4 | u32 | BE | offset_units | [CONFIRMED] | × alignment = offset in logical space |
| 0x08 | 4 | u32 | BE | unknown | [GUESS] | 0 for all 3376 entries |
| 0x0C | 4 | u32 | BE | size | [CONFIRMED] | **exact byte size**. Not in alignment units (see below) |

- The TOC is **sorted by `name_hash` ascending** [CONFIRMED on the dump]; the lookup is probably a binary search [LIKELY, unverified in code].
- Data offsets are **not** in TOC order.
- Data begins at the first 0x800 boundary after the TOC (`0xD800`).
- Each entry is padded to the next 0x800 boundary: for all 3376 entries, `gap_to_next − 0x800 < size ≤ gap_to_next`. The final entry ends at `0x11EB578B4`, and the logical space (sum of parts) ends at `0x11EB58000`.

### Disagreement with prior art
CHoops-Extractor-Reborn reads +0x0C as alignment units, concludes that "stored sizes can be impossible", and derives sizes from the next offset instead. With +0x0C read as bytes, every entry is consistent and none needs a derived size. Their extraction still works because it reads the whole padded extent.

### Round-trip
`ch2k8_archive.py verify` re-serializes the header, part table and TOC from the parsed fields. The result is **byte-identical** (54,120 bytes) on the JB dump.

### Layout rules [CONFIRMED on the JB dump]
- Data starts at the first alignment boundary after the TOC (`0xD800`). The bytes between the TOC end (`0xD368`) and that boundary are zero.
- The layout is **tight**: for all 3,376 entries the gap to the next entry is exactly `align_up(size, 0x800)`.
- Padding after each entry is zero.
- Parts `0A`..`0D` are full (0x80000 units = 1 GiB), and `0E` holds the remainder.

### Full rebuild
`ch2k8_archive.py <usrdir> rebuild -o OUT [--replace FILE...] [--replace-dir DIR] [--check]`

- Keeps the original data order and the TOC (hash) order. Replaced entries may grow or shrink, and everything after them moves. Padding is zero.
- Parts are filled up to the size of the source `0A`. Parts past `0E` are named `0F`, `0G`… [GUESS]. It's unverified whether the game reads the part table or hardcodes the five names, so the tool warns if the part count changes.
- A replacement file matches by its filename's hash, or by the extract fallback name `NNNNN_HASH.bin` for unresolved entries. Names not in the TOC are rejected, because adding new entries isn't supported.
- **An unmodified rebuild is byte-identical** to the 4.8 GB source (`--check`, 2026-10-22). Growing `loading.iff` by 4 KiB moved 3,375 entries. All of them read back unchanged, and the new part table was valid (`0E` grew by 2 units).
- **Not yet boot-tested in RPCS3.** The game might cache offsets, or check sizes or hashes, in ways the format doesn't show.

## Hex example (JB dump, `0A`)

```
00000000: aa00 b3bf 0000 0800 0000 0005 0000 0000   magic, align=0x800, parts=5, 0
00000010: 0000 0d30 0000 0000                       entries=3376, 0
00000018:                     0008 0000 0000 0000   part 0A: 0x80000 units (1 GiB), 0
00000020: 0030 0041 0000 0000                       "0A" UTF-16BE
...
00000058:                     0003 d6b0 0000 0000   part 0E: 0x3D6B0 units = 515,211,264 B
00000060: 0030 0045 0000 0000                       "0E"
00000068:                     0000 f5e6 000d 378e   TOC[0]: hash 0000F5E6, offset 0xD378E units
00000070: 0000 0000 0000 0030                       unknown 0, size 0x30 bytes
```

## Xbox 360 variant [CONFIRMED]
The 360 disc (XGD2, see [xdvdfs.md](xdvdfs.md)) carries **the same archive format** in its root directory,
next to `default.xex`. `ch2k8_archive.py` reads it without changes. Its header, part table and TOC round-trip
byte-identically (54,280 bytes), and `rebuild --check` is IDENTICAL over the full 6.9 GB.

| | PS3 | 360 |
|---|---|---|
| Parts | 5 × 1 GiB (`0A`..`0E`) | 13 × 512 MiB (`0A`..`0M`), last part 50,071,552 B |
| Entries | 3,376 | 3,378 (+`HighlightCreate.iff`, `loading_highlight.iff`) |
| Payload | 4,806 MB | 6,489 MB |
| Byte order | BE | BE (same `FF3BEF94` IFF magic) |

This confirms that part names continue alphabetically past `0E` (`0F`..`0M`), which the rebuild tool already assumed.
The part size is a per-platform choice, and the rebuild tool takes it from the source `0A`.

## Name resolution
Hashes are CRC32 over the uppercased filename, so names must come from candidates. Sources, in the order they were added, with cumulative coverage:

| Source | Named |
|---|---|
| Pattern namespace (`ua###`, `uh###`, `s###`, `h####`, named banks…) | 3097 |
| + CHoops-Extractor-Reborn `names.json` (only pairs whose CRC we reproduce) | 3191 |
| + NBA 2K9 PC filenames | 3285 |
| + generated `shoe_###_##.iff` | 3301 / 3376 |

75 entries remain unresolved.
