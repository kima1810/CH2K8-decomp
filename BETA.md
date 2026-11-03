# College Hoops 2K8 — ZMO beta 1

## Install and play (Windows x64)

1. Extract the entire beta ZIP into a folder you can write to, such as Documents/CH2K8. Avoid Program Files. Keep the executable, DLLs and tools together.
2. Supply your own USA Xbox 360 game data. An extracted disc folder must contain `default.xex`. No game files are included in the beta download.
3. Double-click **Launch CH2K8.cmd**, click **Browse**, and select that folder. Click **Check setup**, then **Launch game**.
4. Start with Direct3D 12, Automatic, 1280x720, 60 Hz, Windowed. Increase resolution or choose borderless after checking gameplay. Accurate Xbox blending is the slower compatibility option. Vulkan remains experimental; folder asset replacements require D3D12.

No compiler or SDK is needed for a prebuilt beta. Extracted disc installations do not need Python. Editable folder installations (`assets.json`) require Python 3.11+ available as `python.exe` on PATH; their edits are validated/prepared before launch. Launching a loose folder does not import an ISO. Source users can import with `python tools/loose_assets.py import "PATH/TO/GAME.iso" "PATH/TO/NEW FOLDER"`; existing destinations are refused.

Settings and saves stay in `port/userdata` beside the launcher. **Saves / settings** opens that folder; back it up before updating. Extract updates to a new folder, then copy your userdata into the same location. Keep game data separately and select it again. Remove the beta folder to uninstall after backing up saves; your separately stored game data remains available.

First startup can take longer while shaders compile. If launch fails, use **Check setup** and confirm the complete ZIP was extracted. **Open logs** opens the selected runtime's logs folder. For a beta report include the version, GPU, renderer, resolution, rendering mode, reproduction steps and runtime log. Review logs for personal paths before sharing. Exit the game before changing runtime files.

## Beta scope

This is an experimental native recompilation. Menu boot and live gameplay have been observed; full-game completion and Legacy are untested. Direct folder resources, growing rosters, native audio replacement and additional texture layouts still need manual in-game acceptance. See `port/README.md` and `docs/formats/loose_assets.md` in the source repository for evidence and limits.

## Build the distributable (maintainers)

Build the current patched dual-backend runtime using `port/README.md`, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/package_beta.ps1
```

The script creates a new timestamped portable ZIP under `out/beta`, containing the executable, required runtime DLLs, launcher, asset preparation tools, version metadata and SHA-256 inventory. It includes no disc data, generated source, saves or developer environment. The source branch does not contain compiled binaries; distribute the ZIP separately after beta acceptance testing. Building from source still requires the SDK and game data described in `port/README.md`.
