# 2026-10-22: Xbox 360 disc inventory

## Question
What is on the CH2K8 Xbox 360 disc, and how much of the PS3 asset work carries over to the port target?

## Method
- `ref/College Hoops 2K8 (USA).7z` now holds the 360 ISO; it was replaced by the user. Extracted with Windows `tar.exe` to `work/ch2k8/XBOX/`.
- Wrote `tools/xdvdfs.py` to list and extract the XGD2 file system into `work/ch2k8/XBOX/disc/`.
- Ran `ch2k8_archive.py info/verify/list/rebuild --check` on the 360 parts. Diffed the entry list against the PS3 listing by name hash, and compared same-size entries byte for byte.
- Parsed the `default.xex` optional headers (format info, base, entry, PE name, exec info, static and import libraries).

## Evidence
- The disc root has `default.xex`, the archive parts `0A`..`0M` (12 × 512 MiB plus 50 MB) and `$SystemUpdate`. There are no loose assets.
- 360 archive: same magic `AA00B3BF`, alignment 0x800, 13 parts, 3,378 entries. The header/TOC round-trip is IDENTICAL, there are 0 size anomalies, the TOC is hash-sorted, the layout is tight (3,378/3,378), and `rebuild --check` is IDENTICAL.
- All 3,376 PS3 hashes exist on the 360. The 360 adds `HighlightCreate.iff` and `loading_highlight.iff`.
- 3,360 / 3,376 shared entries have the same first 4 bytes. The 16 that differ are speech/audio banks: PS3 `Axxxxxxx` vs 360 `08000000`.
- 582 shared entries have the same size, and 539 of those are byte-identical across platforms. The IFF container header is unchanged (e.g. `h0001.iff` is identical, while `ua149.iff` has the same chunk names with different payload sizes).
- Size by type, PS3 → 360: IFF 2,711 → 2,967 MB, CDF 132 → 160 MB, `.bin` 1,051 → 1,739 MB, unresolved 912 → 1,618 MB.
- XEX: XEX2, encrypted and LZX-compressed, base `0x82000000`, image size `0x3E00000`, entry `0x84E04720`. The original name is `ncaabasketball_clean_opt_submission_ready.xex`. Static libraries are all XDK 2.0.5632, and the imports are `xam.xex` and `xboxkrnl.exe`.

## Conclusion
- **Phase 1 tooling carries over to the 360 target unchanged.** It's the same archive, the same big-endian IFF family and the same hashing. The archive reader and rebuild tool already work on the 360 data.
- The platform differences sit inside IFF payloads, likely texture and GPU data (GTF vs Xenos layouts), and in the audio codec of the speech banks (360 `08000000`, likely XMA).
- The XEX is a standard retail title built with the 2.0.5632 XDK, so we need SDK function-ID databases for that XDK version.

## Confidence
- Disc layout, archive identity, entry diff, XEX header fields: [CONFIRMED].
- Payload differences being texture/GPU data: [GUESS], based on the size changes in uniform IFFs and same-size identical heads/scenes. Needs a chunk-level diff.
- 360 audio banks being XMA: [GUESS], based on the platform convention. The `08000000` header isn't decoded yet.

## Open questions
- Chunk-level diff of a 360 vs PS3 IFF: which chunk types change, and what is the 360 texture format?
- Decode the 360 `08000000` audio bank header.
- Decrypt and decompress the XEX locally for Ghidra (XexTool or Xenia). Once that's done, find the archive hash lookup.
- Is there a Ghidra FIDB that matches XDK 2.0.5632 (tomcl7/ghidra-fidb-xenonsdk coverage)?
