# File inventory: CH2K8 (PS3) vs NBA 2K9 (PC)

Generated 2026-10-09 (Phase 0). Raw per-file data is in `work/inventory/` (gitignored):
`ch2k8_entries.csv` (from `tools/ch2k8_archive.py list`) and `nba2k9_files.csv` (from `tools/inventory.py`).
Magics are shown as **raw on-disk bytes**.

## CH2K8 PS3 disc (JB dump)

| Path | Size | Magic | Notes |
|---|---:|---|---|
| `PS3_DISC.SFB` | 1,536 | | disc descriptor |
| `PS3_GAME/PARAM.SFO` | 1,008 | | title metadata |
| `PS3_GAME/ICON0.PNG`, `PS3LOGO.DAT` | | | |
| `PS3_GAME/USRDIR/EBOOT.BIN` | 52,464,616 | `53434500` (`SCE\0`) | encrypted SELF [CONFIRMED]. Needs local decryption before Phase 2 |
| `PS3_GAME/USRDIR/0A`..`0D` | 4 × 1,073,741,824 | `AA00B3BF` (0A only) | one split archive, see [usrdir_archive.md](../formats/usrdir_archive.md) |
| `PS3_GAME/USRDIR/0E` | 515,211,264 | | last part |

There are **no loose asset files**. All 3,376 assets are entries inside the split archive. Together they hold 4,806,156,571 bytes before 0x800 padding.

### Archive entries by extension (names resolved by hash; 3,301 / 3,376)

| ext | count | total bytes | min | max | magics (count) |
|---|---:|---:|---:|---:|---|
| .iff | 3254 | 2,710,908,465 | 48 | 32,430,353 | `FF3BEF94` standard IFF (3214), `F0985030` CDF-backed IFF (39), `E4791207` set/list? (1: `loc.iff`) |
| .bin | 8 | 1,051,042,608 | 127,376 | 548,255,488 | 8 distinct `Axxxxxxx` magics: speech/audio banks? [GUESS] |
| (unresolved) | 75 | 912,071,981 | 474 | 419,558,912 | `FF3BEF94` (65), `A0024E9F` (3), other `Axxxxxxx` (5), H7A (1), CDF-backed (1) |
| .cdf | 39 | 132,133,517 | 76,680 | 27,520,175 | `00000001` audio bank, 48 kHz (28), `0E4837C3` H7A-compressed segment (11) |

### Largest asset families

| Family | Count | MB | Meaning (from CHoops-Extractor-Reborn handoff; [LIKELY]) |
|---|---:|---:|---|
| `s###.iff` | 384 | 1661.8 | arenas/courts (SCNE + TXTR + CDAN) |
| unresolved | 75 | 912.1 | ~880 MB are 8 `Axxxxxxx` banks, likely more speech |
| `lines.bin` | 1 | 548.3 | play-by-play speech? [GUESS from name] |
| `uh###.iff` / `ua###.iff` | 452 / 452 | 324.7 / 287.1 | home/away gameplay uniforms |
| `paplayers.bin`, `players.bin`, `teams.bin`, `palines.bin` | 4 | 494 | PA / commentary name banks? [GUESS] |
| `m###.iff` | 101 | 58.2 | mascots/models |
| `ux###.iff` | 81 | 51.8 | alternate uniforms (sparse) |
| `h####.iff` | 85 | 45.2 | head models |
| `seluh###` / `selua###` / `selux###` | 452 / 452 / 81 | 36.8 / 32.3 / 6.5 | menu uniform previews |
| `coach###.iff` | 50 | 27.9 | coaches |
| `shoe_###_##.iff` | 88 | 2.1 | shoes (same naming as 2K9) |
| named banks | ~100 | | `global`, `gamedata`, `frontend`, `shrine`, `roster_english`, `teamselectlogo`, `arenapics`, `pc*`, `cwd-*` crowd audio… |

## NBA 2K9 PC

3,389 loose files, 8.9 GB.

| ext | count | total bytes | min | max | magics (count) |
|---|---:|---:|---:|---:|---|
| .iff | 3214 | 4,684,482,894 | 32 | 29,921,818 | `94EF3BFF` standard IFF LE (3162), `305098F0` CDF-backed LE (45), `071279E4` set/list LE (7) |
| .bin | 31 | 4,055,332,102 | 27,000 | 747,194,760 | `80808080` (12), `7F7F7F7F` (2), `7F7F7F80` (2), +15 more: audio, different codec from PS3 |
| .cdf | 44 | 520,002,311 | 130,038 | 234,917,888 | `01000000` audio bank LE (26), `0E4837C3` H7A (15, **BE** on PC too), 3 others |
| .exe / .dll | 5 / 2 | ~102 MB | | | `4D5A` PE (x86 code for Phase 2 reference) |
| .cab | 75 | 67.6 MB | | | DirectX/XACT redistributables |
| .bnk | 8 | 14.8 MB | | | `94EF3BFF` (an IFF under another extension) |
| .spc, .txt, .ico | 8 | | | | |

## Side-by-side: shared formats

300 filenames exist in both games (matched by CH2K8 name hash).

| Format | CH2K8 PS3 bytes | 2K9 PC bytes | Relation | Shared files | Confidence |
|---|---|---|---|---:|---|
| Standard IFF | `FF3BEF94` | `94EF3BFF` | byte-swapped (BE ↔ LE) | 279 | [CONFIRMED] |
| CDF-backed IFF | `F0985030` | `305098F0` | byte-swapped | 6 | [CONFIRMED] |
| set/list IFF (`loc.iff`) | `E4791207` | `071279E4` | byte-swapped | 1 | [CONFIRMED] magic; meaning [GUESS] |
| H7A compression wrapper | `0E4837C3` | `0E4837C3` | identical; header is BE on PC too | 6 (`.cdf`) | [LIKELY] |
| CDF audio bank header | `00000001 00000005 0000000F … 0000BB80` | `01000000 …` | byte-swapped | (all `cwd-*`) | [LIKELY] |
| Speech `.bin` banks | `Axxxxxxx` | `80808080` / `7F7F7F7F` / … | **different encoding** | 8 | [LIKELY] different codec per platform |
| Split USRDIR archive | `AA00B3BF` | n/a (PC uses loose files) | PS3 only | | [CONFIRMED] |

No shared file has the same size on both platforms, so content differs even where the format matches.
