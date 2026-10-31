# Building the Xbox 360 recompilation

This is an experimental native port. Successful code generation or compilation
does not establish that menus or gameplay work.

## Prerequisites

- A local USA Xbox 360 disc image. The researched `default.xex` SHA-256 is
  `71e8983d1cc009e485696aad19b5fa4b4661761870e2c8972717b932c1e4be36`.
- Python 3.11+ for disc/archive tools; pytest for the archive tests.
- CMake 3.25+, Ninja, Clang 20+, and Microsoft C++ build tools plus Windows SDK.
- The Windows x64 [ReXGlue SDK nightly-20261002-bd833a2a](https://github.com/rexglue/rexglue-sdk/releases/tag/nightly-20261002-bd833a2a).
  Use `rexglue-sdk-0.10.0.24-dev.gbd833a2-win-amd64.zip`, SHA-256
  `1e19d7ec9be0d9d7e1a0088a34a33b068d4dea520181e81318528ef3b37627e7`.
  Extract its **inner** `win-amd64` directory's contents into `port/sdk/`, so
  `port/sdk/bin/rexglue.exe` exists.

The 2026-10-30 investigation uses Clang 23.1.4, CMake 4.4.4, Ninja 1.13.2,
MSVC tools 14.39.33519, and Windows SDK 10.0.26100.0. This is a tested setup,
not a claim that every combination above the minimum versions works.

## Extract and generate

From the repository root in PowerShell, substituting your own ISO path:

```powershell
python tools/xdvdfs.py 'D:\games\College Hoops 2K8 (USA).iso' extract -o work/ch2k8/XBOX/disc
python tools/ch2k8_archive.py work/ch2k8/XBOX/disc verify
Set-Location port
New-Item -ItemType Directory -Force logs | Out-Null
./sdk/bin/rexglue.exe --log-file logs/codegen.log codegen ch2k8_manifest.toml
```

Extraction never overwrites existing files. Use an empty destination for a new
extraction. ReXGlue accepts the retail XEX directly; a separate decrypted copy
is unnecessary for code generation.

## Configure and compile

Ensure `clang++`, `cmake`, and `ninja` are on PATH. A Visual Studio developer
PowerShell with the x64 C++ environment is appropriate if the compiler cannot
find Microsoft libraries.

From `port/`:

```powershell
cmake --preset win-amd64
cmake --build --preset win-amd64 --parallel 2
```

The initial build compiles about 150 MB of generated C++. Start with two jobs
on a 16 GB machine; one initializer alone generates about 8.8 MB of source.
Do not edit `generated/`: fix analysis in `config/` and regenerate. Generated
files, SDK files, build outputs, logs, and game data are ignored by Git.

The build automatically applies `tools/fix_codegen.py` after code generation.
This narrowly corrects the pinned SDK's invalid 32-bit/44-bit sign-extension
expressions for `vupkd3d128`. It preserves the 64-bit intermediate until the
signed 20-bit lane has been extracted. Numeric regression tests cover positive,
negative, minimum, and maximum lanes. Clang treats any remaining oversized shift
as an error. The correction is idempotent and does not rewrite unrelated code.

`tools/run_codegen.py` preserves the manifest's timestamp when the SDK rewrites
identical content. CMake uses it through a build-directory copy of the generated
SDK boilerplate. It applies the VMX correction before returning to Ninja and
preserves C++ timestamps only when the final corrected bytes are unchanged.
Genuine changes are retained. This avoids making an unchanged project dirty
after every codegen invocation; the original generated boilerplate stays intact.
Windows linking also emits a PDB containing the generated code's line tables.

After a successful build, the executable is `out/build/win-amd64/ch2k8.exe`.
An explicit runtime command is:

```powershell
./out/build/win-amd64/ch2k8.exe --game_data_root ../work/ch2k8/XBOX/disc --gpu_plugin xenos
```

## Verify and investigate

From the repository root:

```powershell
python -m pytest tests -q --basetemp=out/pytest
Get-ChildItem port/generated/default -Filter '*.cpp' | Select-String 'REX_FATAL'
```

No `REX_FATAL` matches are expected after the control-flow fixes. Switch default
traps still exist; removing known fallbacks is not proof of complete coverage.
The PS3 integration test skips when its local dump is absent. The generated
startup-loop execution test additionally needs Windows, the local SDK, and
locally generated sources; it checks that loop indices 8 and 9 no longer trap.

For executable research, Ghidra 12.2 with Java 25 and the matching Xenon360
0.8.2 extension can import the retail XEX. `ghidra/DumpPpcRange.java` accepts
pairs of guest address and byte count, and prints raw big-endian words plus
disassembly. Inline pointer tables are data even when a word also decodes as
an instruction. Keep Ghidra projects and exported game bytes under `work/`.

See [the control-flow investigation](../docs/findings/2026-10-30-native-build-and-control-flow.md)
for the exact sites, table entries, and validation limits.

To audit the exact inline absolute-table idiom, run
`ghidra/ExportInlineSwitches.java` in a read-only Ghidra session, passing an
output TOML path such as `work/inline-switches.toml`. Then compare it from the
repository root:

```powershell
python tools/audit_inline_switches.py work/inline-switches.toml port/generated/default
```

The investigated image has 1,762 recognized tables; the final hints leave zero
truncated prefixes or target/selector disagreements. `--output NEW_FILE.toml`
can propose verified prefix extensions for review; it refuses to overwrite an
existing file. This does not audit other switch forms or arbitrary callbacks.

The final 2026-10-30 startup test stayed alive for 30 seconds after initialization,
then was deliberately stopped. On 2026-10-31, the user confirmed a successful
menu boot. A subsequent gameplay-start attempt crashed on missing callback
`8471B2F0`; its original four-byte tail-call thunk is now registered.
**Gameplay after that fix still requires a retry.** Allocation errors and kernel/network
stubs remain in the earlier logs; their resolution has not been established.
See [the menu-boot finding](../docs/findings/2026-10-31-menu-boot.md).
See [the gameplay-crash finding](../docs/findings/2026-10-31-gameplay-startup-callback.md)
for the observed failure and correction.
