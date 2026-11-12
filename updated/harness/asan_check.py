#!/usr/bin/env python3
"""Build the original code with AddressSanitizer and feed it enough frames to
reach the first filter call. Reports whether ASan flags the out-of-bounds
access in Butterworth.cpp ``filter`` (loop bound ``i < np + 1``).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from build_original import build  # noqa: E402
from heartbeat_port.synthetic import synthetic_ppg_green_components  # noqa: E402


def run() -> tuple[bool, str]:
    exe = build("asan")
    comps = synthetic_ppg_green_components(72, 3, seed=0)  # 90 SYNTHETIC frames
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.txt"
        out = Path(td) / "out.csv"
        inp.write_text("".join(f"{c!r}\n" for c in comps))
        p = subprocess.run([str(exe), "trace", str(inp), str(out)], capture_output=True, text=True)
    report = p.stderr
    flagged = "AddressSanitizer" in report and "filter" in report
    return flagged, report


if __name__ == "__main__":
    flagged, report = run()
    lines = [ln for ln in report.splitlines() if "ERROR: AddressSanitizer" in ln or " in filter" in ln or "WRITE of size" in ln or "READ of size" in ln]
    print("ASan flagged original filter():", flagged)
    print("\n".join(lines[:6]))
