# Findings index

- [2026-10-31 Live gameplay black screen](2026-10-31-live-gameplay-black-screen.md): paused/camera/replay rendering works, live gameplay remains black, and log 010 closes normally. Prepare isolated render-target and shader-compilation comparisons with settings/CPU logging.

- [2026-10-31 Packed vector geometry](2026-10-31-packed-vector-geometry.md): pre-run-out black flash report leads to a verified packed-vector translation error; correct source half, biased float bits, component order and overflow handling. Visual retry remains required.

- [2026-10-31 Gameplay flag callback](2026-10-31-gameplay-flag-callback.md): log 008 reaches `848E3A00`; recovered its flag-bit clearing body and audited 42 nearby code-pointer candidates.

- [2026-10-31 Scripted gameplay callback](2026-10-31-scripted-gameplay-callback.md): the next attempt stops on `84AB8CA8`; verified its global-load/tail-call body and audited 87 code-pointer candidates in the containing data region. Added the sole missing entry; gameplay retry remains required.
- [2026-10-31 Arena introduction callbacks](2026-10-31-arena-intro-callbacks.md): arena/player/crowd presentation is visible with geometry corruption; crash reaches `848B6FA0`. Audited 185 interleaved records and repaired their two missing targets; gameplay retry remains required.
- [2026-10-31 Gameplay startup callbacks](2026-10-31-gameplay-startup-callback.md): successive attempts reach unregistered `8471B2F0` and `8471B2E8`; audited their complete 25-entry family, registered four missing thunks in total, and added calling-convention execution checks. Gameplay retry remains required.
- [2026-10-31 Menu boot](2026-10-31-menu-boot.md): the user confirms a successful native menu boot; a subsequent gameplay attempt and crash are recorded in the callback finding above.
- [2026-10-30 Native build + control-flow recovery](2026-10-30-native-build-and-control-flow.md): native build succeeds; resolved 16 fatal fallbacks, recovered 37 switch tables, corrected VMX shifts and incremental builds, and survived a 30-second startup observation. Menu boot was subsequently user-confirmed; gameplay entry failure and its mapping fix are recorded above.
- [2026-10-09 Phase 0 inventory + USRDIR archive](2026-10-09-phase0-inventory.md): split archive `AA00B3BF` decoded and round-tripped; TOC size is bytes; 300 files shared with 2K9, whose IFFs are byte-swapped.
- [2026-10-22 Port target + archive rebuild](2026-10-22-port-target-and-archive-rebuild.md): the port targets the 360 XEX; the USRDIR archive can now be rebuilt with resized or relocated entries (an identity rebuild is byte-identical; not yet boot-tested).
- [2026-10-22 First ReXGlue codegen](2026-10-22-rexglue-first-codegen.md): ReXGlue reads the retail XEX directly; codegen succeeds with 8 manual function starts (53,803 functions); 16 fatal fallbacks in 3 functions remain.
- [2026-10-22 Xbox 360 disc inventory](2026-10-22-xbox360-disc-inventory.md): the 360 disc uses the same `AA00B3BF` archive (13 × 512 MiB, 3,378 entries) and the PS3 tools work unchanged; audio banks differ; XEX is XDK 2.0.5632.
- [File inventory (CH2K8 vs 2K9)](file_inventory.md): per-extension and per-family tables, plus a side-by-side of shared formats.
