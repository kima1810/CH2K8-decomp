# Port strategy: College Hoops 2K8 on native PC

Decided 2026-10-22: **the code target is the Xbox 360 XEX**, ported through static recompilation.
The PS3 dump is still the main source for asset-format work, which carries over to the 360.

## Goal
Run CH2K8 natively on Windows (later Linux) without an emulator, with loose-file modding,
modern resolutions and an uncapped frame rate. The modding tools stay a standalone deliverable at every phase.

## Why the 360 and not the PS3

| | Xbox 360 (XEX) | PS3 (EBOOT) |
|---|---|---|
| Recompiler | XenonRecomp / ReXGlue are mature, with 50+ shipped ports | ps3recomp is early, with few or no finished ports |
| Second ISA | None. All game code runs on the PPC cores | SPU jobs (likely audio, animation, decompression) must be recompiled separately or rewritten |
| Graphics | Xenos is close to D3D9. XenosRecomp (shaders → HLSL) and ReGPU (D3D12) exist | RSX/libgcm plus compiled Cg, with no existing translation layer |
| Similar games done | NHL Legacy, NHL 14, WWE SvR 2007–2011, Skate 1/2, Tony Hawk's Project 8 | Effectively none |
| Asset formats | Big-endian, same 2K/VC IFF family [LIKELY] | Big-endian, IFF family [CONFIRMED] |

The main costs of choosing the 360: we need a 360 dump, and its data container may not be the
PS3 split archive (see the blockers below).

## Approach: recompile first, decompile later
A matching decomp of a ~50 MB sports-game executable would take years before anything ran.
Static recompilation turns the whole PPC executable into C++ that a native runtime can run.
After that we rewrite subsystems by hand (rosters, Dynasty, renderer) where it pays off,
using the recompiled code as a working reference.

## Phases

### Phase 1: Assets and modding (platform-independent; in progress)
1. Rebuild the full PS3 archive with entries that grow or move (`tools/ch2k8_archive.py rebuild`). Boot-test it in RPCS3.
2. Verify the CHoops-Extractor-Reborn parsers (IFF, CDF, H7A, TXTR/GTF, SCNE, ROST) against the dump, add round-trip tests, and write `docs/formats/` specs.
3. Once the 360 dump exists, inventory its container and IFFs, and diff the formats against the PS3 ones. Textures are the likely difference: GTF/RSX tiling on PS3 vs Xenos tiling on 360.
4. Name the 75 unresolved archive entries from executable strings.

### Phase 2: Executable analysis (360 XEX)
1. Decrypt and decompress the XEX locally (XexTool or Xenia). Never commit the output.
2. Load it in Ghidra with the Xenon360 extension (VMX128 support) and the Xbox 360 SDK FIDBs, so CRT and SDK functions are named automatically.
3. Find the anchor functions: the file/archive lookup (CRC32 of the uppercased name, see `docs/formats/usrdir_archive.md`), the IFF loader, the allocator, the main loop, renderer init, input and audio.
4. Cross-reference against NBA 2K9 PC (`nba2k9.exe`: unpacked x86, the PDB path is present but the PDB isn't): strings, `VCFILE` sites, constant tables, struct layouts.
5. Record names in `docs/symbols/symbols.csv` and structs in `docs/symbols/structs.h`, with confidence tags.

### Phase 3: Recompilation
1. Set up the project on the ReXGlue SDK, using an existing sports recomp (WWE SvR 2008, NHL Legacy) as a template.
2. Run XenonRecomp over the XEX. Recover jump tables (`xenon-jumptables`), fix function boundaries and mid-function entry points, and iterate until everything compiles.
3. Build the runtime layer:
   - kernel/XAM HLE (borrow from the Xenia and ReXGlue implementations)
   - file I/O redirected to the dump's data, plus a loose-file override directory
   - input through SDL, mapped to XInput
4. Graphics: ReGPU (Xenos → D3D12) with XenosRecomp shaders. A custom Vulkan or D3D12 renderer is optional later.
5. Audio: XMA decoding (the FFmpeg decoder or the ReXGlue path). The speech/commentary banks are the open risk.
6. Milestones: boot to the legal screens, then the main menu, then an exhibition game, then Dynasty mode and save data.

### Phase 4: PC-native features
- A loose-file mod loader that replaces archive repacking.
- Arbitrary resolution and aspect ratio, uncapped frame rate, remappable controls, PC-style save location.
- Gradual hand decompilation of the systems modders care about (roster/team data, sliders, Dynasty).

## Effort (rough, for one or two people part-time)

| Step | Estimate | Confidence |
|---|---|---|
| Phase 1 core (archive rebuild, IFF, textures, rosters) | weeks | [LIKELY]; much of it exists as prior art |
| Phase 2 anchors and subsystem map | 1–2 months | [GUESS] |
| Phase 3 to the main menu | 2–4 months | [GUESS]; comparable sports recomps took roughly this long |
| Phase 3 to a stable full game | 6–12 months | [GUESS] |

## Blockers and risks
- **Need a 360 dump** of CH2K8 (ISO or extracted GOD), from a legally owned copy. Nothing in `ref/` covers the 360.
- **The 360 data container is unknown.** It may be a split archive like the PS3's or loose files. Phase 1 tools may need a 360 front end.
- **XMA speech banks**: decoding is solved in general, but 2K's bank layout isn't.
- **Online or 2K Share features** will be stubbed out.
- **Existing effort**: `kima1810/CH2K8-decomp` claims to be a 360 decompilation. Check it before duplicating work.

## Decisions log
- 2026-10-22: the code target is the Xbox 360 XEX via static recompilation (XenonRecomp/ReXGlue). The PS3 path is shelved for code, and the PS3 dump stays the asset reference.
