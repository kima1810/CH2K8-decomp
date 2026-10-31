# 2026-10-31: Live gameplay black screen

## Question and observed behavior

After packed-vector fixes, the user reports correct rendering in camera
settings and replay, but a black screen in live on-court gameplay. The supplied
pause screenshot shows a coherent court, players and crowd. Game startup is
also laggy, with several seconds of black output. These observations are
**[CONFIRMED]** as user-reported behavior, not an independently reproduced trace.
The user clarifies that gameplay continues while the entire image, including
the HUD, is black. An earlier answer saying the HUD was visible was explicitly
corrected. Do not narrow this to court geometry or claim controls stop.

`ch2k8_010.log` starts at 13:28:55 and closes normally at 13:31:14. There is
no fatal callback error in this attempt. Cached shaders translate in 4 ms and
259 cached pipelines initialize in 23 ms; these startup cache timings do not
measure new pipelines, game-data loading, or the transition into gameplay.

## Method and hypotheses

The visible paused scene establishes that some scene rendering works; it does
not prove the live camera, live rendering passes, or final output are correct.
Neither missing assets nor a complete GPU failure is established.

Two bounded runtime comparisons are prepared:

1. `rov`: set only `render_target_path_d3d12=rov`, retaining the other settings.
   This compares pixel-shader interlock with the default host render targets
   on the user's AMD adapter. It may be slower and is a diagnostic, not a
   performance recommendation or a proven fix.
2. `synchronous`: disable only asynchronous shader compilation. The inspected
   D3D12 command processor skips a draw while an asynchronous pipeline handle
   has no ready pipeline state. This can explain temporary missing output,
   but has not been shown to explain persistent black live gameplay. Blocking
   compilation may increase stalls.

`baseline` applies neither override. All profiles use the same user-data and
cache location, preserving saves. Warm caches can affect later comparisons;
keep the matchup and camera consistent and record cold/warm conditions.

## Instrumentation and validation

`tools/launch_render_diagnostic.ps1` creates timestamped run folders under
`port/out/render-diagnostics/` containing the executable SHA-256, arguments,
runtime log and sampled process CPU time/memory/thread counts. CPU samples
are not GPU frame times or proof of the bottleneck. No shader caches are
deleted and no save files are reset.

The pinned release SDK recognizes `perf_log_csv`, but the initial smoke test
produced no CSV. Its performance-counter frame writes are guarded by a build
option disabled in Release, and the inspected source does not connect that
flag to opening the CSV. Consequently the diagnostic uses independent process
samples rather than claiming frame counters are available.

The app now logs effective GPU settings after plugin registration, allowing
each profile to be verified. A 15-second hidden ROV startup test stayed alive
until deliberately stopped and logged `render_target_path_d3d12=rov` with
async compilation still true. This does not validate live gameplay output.
The host rebuild succeeds. A separate GUI-subsystem stub verifies the launcher
under Windows PowerShell: paths with spaces remain intact, the requested
profile is passed, process samples are written, and normal exit is awaited.
No full gameplay simulation or measured performance improvement is claimed.

## Conclusion and open questions

The earlier geometry corruption has improved in the supplied paused view.
Persistent black live output and startup stalls remain unresolved. The first
interactive comparison is ROV; its result determines whether to investigate
render-target handling or continue with camera/output-state and pipeline
timing evidence. Do not combine overrides before isolating their effects.
Since the HUD also disappears while gameplay continues, investigate shared
output and full-screen passes alongside scene/camera state; this observation
alone does not identify a defective pass or prove a GPU-backend bug.
