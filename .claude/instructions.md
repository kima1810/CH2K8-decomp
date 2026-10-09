# College Hoops 2K8 Reverse Engineering & PC Port

## Mission
Reverse engineer **College Hoops 2K8 (PS3)** to (1) document and tool its file formats so modding is simple, and (2) build a path to running it natively on PC. Modding tooling is the near-term deliverable; the PC port is the long-term goal. Every phase must produce something usable on its own.

## Ground Truth — Read These First (every new session)
| Resource | Path | Use |
|---|---|---|
| CH2K8 PS3 dump (JB folder) | `ref/College Hoops 2K8 (USA).7z` | Primary target. `PS3_GAME/USRDIR/` holds `EBOOT.BIN` plus split archive `0A`..`0E` (see `docs/formats/usrdir_archive.md`). Extracted copy: `work/ch2k8/`. |
| NBA 2K9 PC | `ref/Nba 2k9.rar` | Sister title, same Visual Concepts engine era, x86 build. Use to identify engine systems, file formats, and naming. Extracted copy: `work/nba2k9/Nba 2k9/`. |
| IFF format notes | `ref/docs/iff-structure.txt` | Authoritative starting spec for 2K IFF containers. Extend it; don't contradict it without evidence. |
| Useful links | `ref/docs/links.md` | Community tools and prior research. Check here before inventing a tool. |
| Prior-art tool | `work/third_party/CHoops-Extractor-Reborn/` | Clone of ZMO34/CHoops-Extractor-Reborn; `docs/MASTER_HANDOFF.md` is a large format research record. Treat as [LIKELY], verify. |
| Findings log | `docs/findings/` | Everything we've learned. Read `docs/findings/INDEX.md` before starting work. |

If a path above doesn't exist, ask me for the real location; never guess. Update this table when paths change.

## Hard Rules
1. **Never modify anything under `ref/`.** It's read-only source material. Work on copies in `work/` (gitignored).
2. **Never commit game data or binaries** (EBOOT, ELF, PRX/SPRX, IFF, textures, audio, decrypted output). Git holds only our code, docs, schemas, and patches. Keep `.gitignore` covering `ref/`, `work/`, `out/`, `*.elf`, `*.self`, `*.bin`, `*.iff`, `*.sprx`, `*.prx`.
3. **No encryption keys or console-specific secrets in the repo.** Decryption of EBOOT happens with tools I run locally (RPCS3's decrypt feature or equivalent); scripts take the decrypted ELF path as input.
4. **Evidence over assumption.** Every format field, function name, or struct member is tagged with a confidence level (below). Never present a guess as fact.
5. **Endianness is explicit, always.** PS3 data is **big-endian**; PC/2K9 is **little-endian**. Every parser/struct declares byte order. Never rely on native order.
6. **Small, verifiable steps.** A format parser isn't done until it round-trips (parse → write → byte-identical output) on real files.
7. **When stuck after two attempts, stop and report** what you tried, what you observed, and your best hypotheses. Don't thrash.

## Confidence Tags
Use in code comments, Ghidra names, and findings docs:
- `[CONFIRMED]` — verified by round-trip, runtime observation (RPCS3), or exact match with 2K9.
- `[LIKELY]` — strong evidence (string refs, matching 2K9 pattern, consistent across many files).
- `[GUESS]` — hypothesis; must include the reasoning.

## Target Platform Facts
- **CPU:** Cell Broadband Engine. PPU = 64-bit PowerPC (big-endian, 32-bit pointers in the PS3 ABI). SPU = separate ISA with local-store code; expect some engine work (audio, physics, animation, decompression) offloaded to SPU.
- **Executable:** `EBOOT.BIN` is an encrypted SELF. Analysis requires the decrypted ELF. System library calls go through imports identified by **NIDs** (FNIDs), so resolve them with a NID database before naming anything.
- **Graphics:** RSX (NV47-derived) via libgcm. Shaders are compiled Cg; PC port will need translation or replacement.
- **Reference build:** NBA 2K9 PC is 32-bit x86/D3D9. Cross-arch, so byte-level diffing won't work; match via **strings, constants, magic numbers, table layouts, call-graph shape, and file formats**.
- **Note:** CH2K8 also shipped on Xbox 360. If the PS3 path stalls (especially on SPU code), flag it; 360 PPC-only code may be more tractable for static recompilation.

## Toolchain (prefer existing tools; check `ref/docs/links.md` first)
- **Static analysis:** Ghidra with a PS3 ELF/PRX loader plugin (PPC64 big-endian, Cell). Use headless Ghidra scripts (Python/Java) for anything repeatable.
- **Dynamic analysis:** RPCS3 debugger and logs for confirming behavior, watching file I/O, and testing patches (RPCS3 patch YAML for in-emulator mods).
- **Our tooling:** Python 3.11+ for format tools (use `struct` with explicit `>`/`<`, or `construct`). C/C++ (CMake) for anything performance-critical or port-related.
- Before writing a new parser, search for an existing community tool for 2K IFF / NBA 2K modding and document whether it works on CH2K8.

## Phased Plan (work in order; don't skip ahead)
**Phase 0: Inventory**
- Walk `USRDIR`, catalog every file: extension, size, magic bytes, count. Output `docs/findings/file_inventory.md`.
- Same for 2K9 PC data. Produce a side-by-side table of shared formats.

**Phase 1: Asset formats → modding tools** (highest priority for real-world value)
- IFF containers first (spec in `ref/docs/iff-structure.txt`): list, extract, rebuild. Handle compression found inside (expect zlib/deflate; verify).
- Then by value to modders: rosters/player data, team data, textures (expect RSX/DXT-style formats with PS3 swizzling), uniforms/courts, audio last.
- Each format gets: a spec doc in `docs/formats/<format>.md`, a parser/writer in `tools/`, round-trip tests in `tests/`.
- Validate by modifying a file, rebuilding, and confirming in RPCS3.

**Phase 2: Executable analysis**
- Decrypted ELF into Ghidra. Resolve NID imports first.
- Map subsystems top-down: file I/O & IFF loader (anchor to Phase 1 knowledge), memory allocator, main loop, renderer init, input, audio, SPU job dispatch.
- Use 2K9 PC strings/asserts/debug messages to name functions. Record every named function in `docs/symbols/symbols.csv` (address, name, confidence, evidence).
- Define recovered structs in `docs/symbols/structs.h` (big-endian notes inline).

**Phase 3: Port strategy** (decide with me, don't start unilaterally)
- Write `docs/port_strategy.md` evaluating: static recompilation of PPU code (XenonRecomp/N64Recomp-style), SPU handling (recompile vs. HLE-reimplement), graphics (libgcm → modern API translation layer), and OS/library HLE. Include effort estimates and blockers.
- Interim win: RPCS3 patches for mod loading (e.g., loose-file override of IFF assets) so modding works before any port exists.

## Repository Layout
```
ref/            # read-only source material (gitignored)
work/           # scratch copies, extracted assets (gitignored)
out/            # build output (gitignored)
tools/          # Python/C++ tools, one module per format
tests/          # round-trip and parser tests (pytest), run against files in work/
ghidra/         # headless scripts, exported (non-binary) project data
docs/
  findings/     # dated research notes + INDEX.md
  formats/      # one spec per file format
  symbols/      # symbols.csv, structs.h
  port_strategy.md
```

## Conventions
- **Findings notes:** `docs/findings/YYYY-MM-DD-<topic>.md`, each with: Question, Method, Evidence, Conclusion, Confidence, Open questions. Add a one-line entry to `INDEX.md`.
- **Function names:** `Subsystem_Action` (e.g., `IFF_LoadChunk`, `Roster_ParsePlayer`). Unknowns stay `FUN_xxxxxxxx` until there's evidence; never invent a name to look tidy.
- **Format specs:** offset table (offset, size, type, endianness, name, confidence, notes) plus a hex example from a real file.
- **Tools:** CLI with `argparse`, `--help`, never overwrite input, write to `work/` or an explicit `-o`.
- **Commits:** small, one logical change, message prefixed by area (`iff:`, `ghidra:`, `docs:`, `roster:`).

## Session Workflow
1. Read `docs/findings/INDEX.md` and the latest findings note.
2. State the goal for this session and which phase it serves.
3. Do the work; verify (round-trip test, RPCS3 check, or cross-reference with 2K9).
4. Write/update the findings note, specs, and `symbols.csv`.
5. End with: what was learned, confidence, what's next, anything blocking that needs me.

## Things to Ask Me Instead of Guessing
- Real paths to reference material, or anything missing from `ref/`.
- Anything needing a runtime test in RPCS3 that you can't run.
- Phase 3 architecture decisions.
- Any action that would touch files outside the repo.