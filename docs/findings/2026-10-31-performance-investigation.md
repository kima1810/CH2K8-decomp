# 2026-10-31: ROV slowdown investigation

## Question and scope

Investigate startup stalls and slow live gameplay while preserving the
user-validated ROV rendering path. No measured performance improvement is
claimed in this first profiling pass.

## Confirmed setup

- The native executable uses CMake Release with `-O3 -DNDEBUG`, not a debug build.
- Host CPU: i7-10700F, 8 cores / 16 logical processors; GPU: RX 6650 XT.
- Portable PresentMon 2.6.0 is downloaded from its official GitHub release,
  not installed system-wide. SHA-256:
  `b2a706bc6ad475749e3b7e3409263aa1e6906d45bdcf993f6dbc0f660188f1af`.
- The capture filters CH2K8; the integrated launcher uses the specific process
  ID and its own named ETW session, avoiding unrelated applications/sessions.

## Measurements and limits

The first capture (`20261031-134952-performance`) contains 24,328 host
presentation records on one swap chain before a new native trap interrupts
the game at approximately 45 seconds. It is **not sustained gameplay evidence**.
The user has not yet identified the precise action at the interruption.

In the PresentMon timeline's 15–40 second window, 7,154 records span 25 seconds:

| Metric | Median | 95th percentile |
|---|---:|---:|
| Host present interval | 5.471 ms | 5.590 ms |
| GPU busy per host present | 0.324 ms | 1.257 ms |
| GPU time per host present | 0.324 ms | 4.440 ms |
| Present API time | 0.046 ms | 0.402 ms |

There are about 286 host presentation calls per second in this window. This
is not gameplay FPS: the presenter can submit repeated images and separate
UI work. Neither these GPU timings nor process CPU averages establish the
on-court bottleneck. In particular, the captured startup window does not
demonstrate GPU saturation.

The inspected SDK presenter explicitly uses DXGI `Present(0, ...)`. It permits
presentation from the guest-output thread, while its UI-thread path has tick
limiting. These are investigation leads, not proof that reducing host presents
will accelerate guest simulation or ROV scene work.

## Profiling blocker repaired

Windows reports C000001D at executable RVA `728961`. PDB mapping and native
disassembly identify a generated `ud2` in `sub_84C1EAA8`, not a GPU-driver crash.
Read-only Ghidra verifies the second dispatch at `84C1EBAC` reads eleven words
at `[84C1EBB0,84C1EBDC)`, but generation emitted only case zero. The remaining
original targets are documented in `control_flow.toml`.

The table is followed by an earlier dispatch's case code before its own first
target. Therefore it is outside the exact self-contained inline-table idiom
recognized by the existing 1,762-table audit. That audit's zero disagreements
did not cover this layout. The final shared epilogue ends at `84C1F038`, where
the next independent prologue begins. Add that function bound and all eleven
table entries; preserve original behavior rather than bypassing the trap.

Native rebuild passes. A generated-output regression checks the owning function,
selector, and all eleven original targets. Full suite: **31 passed, 1 skipped**.
The existing inline audit still compares 1,762 tables without disagreement.
The repaired dispatch needs an interactive retry.

## Reproducible next comparison

The diagnostic launcher now captures PresentMon when the verified local binary
is present, plus process CPU/memory samples. It records trace errors explicitly;
ETW access can require an administrator shell. A restricted smoke test denied
ETW, while an unrestricted smoke test started successfully. No account groups
or machine security settings are changed.

- `-Profile rov`: unchanged working rendering path, now with timing capture.
- `-Profile rov-ui`: keep ROV, change only `host_present_from_non_ui_thread`
  to false. This is an unproven presentation-scheduling experiment.
- Existing `baseline` and `synchronous` profiles remain available; neither
  restores the validated ROV path automatically.

`tools/summarize_presentmon.py` handles BOM headers, unavailable GPU values,
separate swap chains and bounded timeline windows. Its rate is explicitly
labelled host presents per second. Normal launcher behavior remains ROV.

Use the same matchup, camera, window size and warm-cache state. Capture a slow
live segment, then pause and replay, recording the approximate transition
times. Compare GPU busy/wait with CPU/thread activity before changing
readback, memory coherency, assets or graphics correctness settings. Do not
disable required readback merely because it may stall.

## Confidence and outstanding work

Build flags, captured timing statistics and the missing switch entries are
**[CONFIRMED]**. Presentation overhead contributing to the reported slowdown
is **[GUESS]** until a comparable live-game capture shows the effect.
Sustained gameplay profiling and a demonstrated speedup remain outstanding.

Primary tool documentation:
[PresentMon console application](https://github.com/GameTechDev/PresentMon/blob/v2.6.0/README-ConsoleApplication.md).
