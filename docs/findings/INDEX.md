# Findings index

- [2026-10-30 Native build + control-flow recovery](2026-10-30-native-build-and-control-flow.md): native build succeeds; resolved 16 fatal fallbacks, recovered 37 switch tables, corrected VMX shifts and incremental builds, and survived a 30-second startup observation; menus/gameplay remain unverified.
- [2026-10-09 Phase 0 inventory + USRDIR archive](2026-10-09-phase0-inventory.md): split archive `AA00B3BF` decoded and round-tripped; TOC size is bytes; 300 files shared with 2K9, whose IFFs are byte-swapped.
- [2026-10-22 Port target + archive rebuild](2026-10-22-port-target-and-archive-rebuild.md): the port targets the 360 XEX; the USRDIR archive can now be rebuilt with resized or relocated entries (an identity rebuild is byte-identical; not yet boot-tested).
- [2026-10-22 First ReXGlue codegen](2026-10-22-rexglue-first-codegen.md): ReXGlue reads the retail XEX directly; codegen succeeds with 8 manual function starts (53,803 functions); 16 fatal fallbacks in 3 functions remain.
- [2026-10-22 Xbox 360 disc inventory](2026-10-22-xbox360-disc-inventory.md): the 360 disc uses the same `AA00B3BF` archive (13 × 512 MiB, 3,378 entries) and the PS3 tools work unchanged; audio banks differ; XEX is XDK 2.0.5632.
- [File inventory (CH2K8 vs 2K9)](file_inventory.md): per-extension and per-family tables, plus a side-by-side of shared formats.
