# 2026-10-31: Gameplay startup missing callback

## Question

Why does the user-confirmed menu build black-screen and terminate when gameplay starts?

## Method

- Inspected the user's latest local runtime log, `ch2k8_004.log`, and its
  corresponding Windows Application Error record.
- Compared the reported guest target with the generated registration table.
- Inspected the original target and surrounding entries in Ghidra using
  `DumpPpcRange.java` in a read-only session.
- Added a precise function hint and rebuilt with the existing Windows preset.

## Evidence

- The user reports a black screen and crash when starting gameplay.
- The run begins at 12:16:22 on 2026-10-31 and terminates at 12:17:17.
- The last runtime message is:
  `Call to invalid or unregistered function at guest address 0x8471B2F0`.
- Windows records exception `C0000409` in `ucrtbase.dll`, consistent with the
  runtime fatal termination. This record alone does not identify a graphics fault.
- The old generated mappings include neighboring `8471B2E0` and `8471B2F8`,
  but omit `8471B2F0`.
- At `8471B2F0`, the original big-endian instruction word is `4BFFDB30`:
  an unconditional, non-linking branch to `84718E20`. The next word, at
  `8471B2F4`, is zero padding. The destination already has a registered function.

## Correction

Added `0x8471B2F0 = { size = 4 }` to `port/config/pointer_funcs.toml`.
This registers the original tail-call thunk and preserves its destination and
guest calling convention. It does not synthesize a return value or bypass the
destination function.

## Validation

- Windows code generation, compilation, and link: **PASS** with the pinned SDK.
- `PPCFuncMappings` now contains `8471B2F0`, and generated registration calls
  `SetFunction` for it. The generated body calls `sub_84718E20` and returns.
- Regression suite: **22 passed, 1 skipped** (the absent PS3 dump).
- Recognized inline tables: **1,762 compared**, zero truncations or disagreements.
- Generated `REX_FATAL` fallbacks: **0**.

A gameplay retry is required to establish whether execution passes this point
and whether another failure follows. No post-fix successful court load or
gameplay result is claimed.

## Confidence

- Missing runtime target and original branch instruction: **[CONFIRMED]**.
- The registration hint addresses the specific observed fatal dispatch:
  **[CONFIRMED]** structurally; successful gameplay remains unverified.
- The existing physical-memory protection warnings do not establish the cause
  of this fatal dispatch and are not changed by this correction.

## Open questions

- Does the rebuilt executable reach the court and allow play?
- Are additional callback targets or other paths reached only during gameplay?
- Can a complete exhibition game and Legacy save/load succeed?

Prior milestone: [user-confirmed menu boot](2026-10-31-menu-boot.md).
