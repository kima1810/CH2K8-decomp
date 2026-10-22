# Xbox 360 disc image (XDVDFS / XGD2)

Tool: [`tools/xdvdfs.py`](../../tools/xdvdfs.py) (`list`, `extract`). This is a public format, documented here only as far as we use it.

**Endianness: little-endian** (unlike the game data on the disc, which is big-endian).

## CH2K8 image
- `College Hoops 2K8 (USA).iso`: 7,835,492,352 bytes, an XGD2 full-disc rip. The game partition starts at **`0xFD90000`** [CONFIRMED: magic found there].
- Root directory: sector `0x1728BE`, 2,048 bytes.

| Path | Size | Magic | Notes |
|---|---:|---|---|
| `default.xex` | 38,424,576 | `XEX2` | game executable, see below |
| `0A`..`0L` | 12 × 536,870,912 | `AA00B3BF` (0A) | split archive, see [usrdir_archive.md](usrdir_archive.md) |
| `0M` | 50,071,552 | | last archive part |
| `$SystemUpdate/su20076000_00000000` | 7,303,168 | `PIRS` | dashboard update, not game data |

## Volume descriptor (sector 32 of the partition)

| Offset | Size | Type | Endian | Name | Confidence |
|---|---|---|---|---|---|
| 0x000 | 20 | char[20] | | `MICROSOFT*XBOX*MEDIA` | [CONFIRMED] |
| 0x014 | 4 | u32 | LE | root dir sector | [CONFIRMED] |
| 0x018 | 4 | u32 | LE | root dir size | [CONFIRMED] |
| 0x01C | 8 | u64 | LE | FILETIME | [LIKELY] |

## Directory entry (binary tree, 4-byte aligned, `0xFF` sector fill)

| Offset | Size | Type | Endian | Name | Confidence |
|---|---|---|---|---|---|
| 0x00 | 2 | u16 | LE | left subtree, in dwords | [CONFIRMED] |
| 0x02 | 2 | u16 | LE | right subtree, in dwords | [CONFIRMED] |
| 0x04 | 4 | u32 | LE | start sector | [CONFIRMED] |
| 0x08 | 4 | u32 | LE | size in bytes | [CONFIRMED] |
| 0x0C | 1 | u8 | | attributes (`0x10` = dir) | [CONFIRMED] |
| 0x0D | 1 | u8 | | name length | [CONFIRMED] |
| 0x0E | n | char | | name | [CONFIRMED] |

Confirmed by `extract`: the archive extracted from the image is read by `ch2k8_archive.py` with a byte-identical header round-trip.

## default.xex header (XEX2, big-endian)

| Field | Value | Confidence |
|---|---|---|
| Original PE name | `ncaabasketball_clean_opt_submission_ready.xex` | [CONFIRMED] |
| Encryption / compression | 1 (encrypted) / 2 (normal, LZX) | [CONFIRMED] header fields |
| Image base / image size | `0x82000000` / `0x3E00000` (62 MB) | [CONFIRMED] |
| Entry point | `0x84E04720` | [CONFIRMED] header field |
| Title ID | `54540818` (exec info, version 2) | [LIKELY] |
| Static libs | D3D9, LIBCMT, X3DAUD, XAPILIB, XAUD, XBOXKRNL, XGRAPHC, XHV, XMP, XNET, XONLINE, all **XDK 2.0.5632** | [CONFIRMED] |
| Imports | `xam.xex`, `xboxkrnl.exe` | [CONFIRMED] |

The internal name `ncaabasketball_clean_opt` matches 2K9 PC's `nba_clean_opt.exe.pdb`: the same VC build pipeline and config names.
