#!/usr/bin/env python3
"""Compile the UNMODIFIED original Butterworth.cpp + Algorithm.mm into a macOS
reference executable (``updated/build/heartbeat_trace[_strict|_asan]``).

Variants:
  strict   -ffp-contract=off: IEEE per-operation rounding, the variant the
           Python port is expected to match bit-for-bit.
  default  Apple clang defaults (may fuse multiply-adds on arm64).
  asan     AddressSanitizer build used to confirm the original one-past-the-end
           write in Butterworth.cpp's ``filter``.

Only Apple clang (Xcode command-line tools) and Foundation are required.
The original files are read from ../source and never written.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPDATED = HERE.parent
SOURCE = UPDATED.parent / "source" / "Heartbeat"
BUILD = UPDATED / "build"

VARIANTS = {
    "strict": ["-O2", "-ffp-contract=off"],
    "default": ["-O2"],
    "asan": ["-O1", "-g", "-fsanitize=address", "-fno-omit-frame-pointer", "-ffp-contract=off"],
}


def compiler() -> str | None:
    return shutil.which("clang++")


def build(variant: str = "strict", verbose: bool = False) -> Path:
    cxx = compiler()
    if cxx is None:
        raise RuntimeError("clang++ not found")
    if not (SOURCE / "Algorithm.mm").exists():
        raise RuntimeError(f"original source not found at {SOURCE} (init the git submodule)")
    BUILD.mkdir(exist_ok=True)
    flags = VARIANTS[variant]
    exe = BUILD / f"heartbeat_trace_{variant}"
    objs = []
    common = ["-std=c++17", "-w", f"-I{SOURCE}", f"-I{HERE}"] + flags
    jobs = [
        (SOURCE / "Butterworth.cpp", ["-x", "c++"]),
        (SOURCE / "Algorithm.mm", ["-x", "objective-c++", "-fobjc-arc", "-include", str(HERE / "uikit_shim.h")]),
        (HERE / "trace_main.mm", ["-x", "objective-c++", "-fobjc-arc"]),
    ]
    for src, lang in jobs:
        obj = BUILD / f"{src.stem}_{variant}.o"
        cmd = [cxx, *lang, *common, "-c", str(src), "-o", str(obj)]
        if verbose:
            print(" ".join(cmd))
        subprocess.run(cmd, check=True)
        objs.append(str(obj))
    link = [cxx, *flags, *objs, "-framework", "Foundation", "-o", str(exe)]
    if verbose:
        print(" ".join(link))
    subprocess.run(link, check=True)
    return exe


if __name__ == "__main__":
    variants = sys.argv[1:] or ["strict", "default"]
    for v in variants:
        print("built", build(v, verbose=True))
