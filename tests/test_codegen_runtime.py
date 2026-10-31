"""Optional execution checks against locally generated code; no game data committed."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def test_generated_startup_loop_reaches_cases_eight_and_nine(tmp_path):
    root = Path(__file__).resolve().parents[1]
    generated = root / "port/generated/default"
    sdk = root / "port/sdk/include"
    compiler = shutil.which("clang++")
    if sys.platform != "win32" or not compiler or not sdk.is_dir() or not generated.is_dir():
        pytest.skip("Requires Windows, local ReXGlue SDK, generated game code, and clang++")
    signature = "DEFINE_REX_FUNC(sub_84D36860) {"
    body = None
    for path in generated.glob("*_recomp.*.cpp"):
        source = path.read_text(encoding="utf-8")
        if signature in source:
            start = source.index(signature)
            body = source[start:source.index("\n}\n", start) + 3]
            break
    assert body is not None, "Startup loop missing from generated code"

    # Independent layout calculation from the original ten-entry tables.
    alignment = [16, 16, 1, 52, 16, 16, 1, 52, 4, 4]
    count = [256, 32, 128, 26, 256, 32, 128, 10, 96, 4]
    size = 200
    for index in range(10):
        if index in (3, 7):
            continue
        unit = alignment[index]
        size = ((size + unit - 1) // unit) * unit + unit * count[index]
        size = ((size + 7) // 8) * 8 + ((count[index] + 63) // 64) * 16
    expected = ((size + 3) // 4) * 4 + 512
    assert expected == 10864

    source = tmp_path / "startup_loop.cpp"
    executable = tmp_path / ("startup_loop.exe" if sys.platform == "win32" else "startup_loop")
    source.write_text(
        '#include "ch2k8_pch.h"\n#include <windows.h>\n' + body + "\n"
        "int main() { PPCContext ctx{};\n"
        "auto memory = static_cast<uint8_t*>(VirtualAlloc(nullptr, 1ull << 32, MEM_RESERVE, PAGE_NOACCESS));\n"
        "if (!memory) return 2;\n"
        "if (!VirtualAlloc(memory + 0x84D36000u, 4096, MEM_COMMIT, PAGE_READWRITE)) return 3;\n"
        "sub_84D36860(ctx, memory);\n"
        "VirtualFree(memory, 0, MEM_RELEASE);\n"
        f"return ctx.r3.u32 == {expected} ? 0 : 1; }}\n",
        encoding="utf-8",
    )
    compilation = subprocess.run(
        [compiler, "-std=c++23", "-O2", "-msse4.1", "-DNOMINMAX", "-DWIN32_LEAN_AND_MEAN",
         "-DSPDLOG_FMT_EXTERNAL", "-DSPDLOG_COMPILED_LIB",
         "-I", str(sdk), "-I", str(generated), str(source), "-o", str(executable)],
        capture_output=True, text=True,
    )
    assert compilation.returncode == 0, compilation.stderr
    execution = subprocess.run([str(executable)], capture_output=True, text=True)
    assert execution.returncode == 0, f"Generated loop failed: {execution.returncode}, {execution.stderr}"
