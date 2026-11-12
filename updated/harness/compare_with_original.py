#!/usr/bin/env python3
"""Run the compiled ORIGINAL HeartBeat code and the Python port on the same
SYNTHETIC inputs and report differences. Builds the harness if needed.

Usage: python3 harness/compare_with_original.py [strict|default]
"""

from __future__ import annotations

import csv
import dataclasses
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from build_original import BUILD, build  # noqa: E402
from heartbeat_port import butter  # noqa: E402
from heartbeat_port.algorithm import run_on_green_components  # noqa: E402
from heartbeat_port.synthetic import synthetic_ppg_green_components  # noqa: E402

FIELDS = [f.name for f in dataclasses.fields(__import__("heartbeat_port").FrameTrace)]


def ensure_exe(variant: str) -> Path:
    exe = BUILD / f"heartbeat_trace_{variant}"
    if not exe.exists():
        build(variant)
    return exe


def original_coeffs(variant: str = "strict"):
    exe = ensure_exe(variant)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "coeffs.csv"
        subprocess.run([str(exe), "coeffs", str(out)], check=True, stdout=subprocess.DEVNULL)
        rows = list(csv.DictReader(out.read_text().splitlines()))
    return [float(r["b"]) for r in rows], [float(r["a"]) for r in rows]


def original_trace(components, variant: str = "strict", window_size: int = 0, filter_window_size: int = 0):
    exe = ensure_exe(variant)
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.txt"
        out = Path(td) / "out.csv"
        inp.write_text("".join(f"{c!r}\n" for c in components))
        cmd = [str(exe), "trace", str(inp), str(out)]
        if window_size or filter_window_size:
            cmd += [str(window_size), str(filter_window_size)]
        # the original prints peak indices / "missed peak" to stdout; discard
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        rows = list(csv.DictReader(out.read_text().splitlines()))
    return [{k: float(v) for k, v in r.items()} for r in rows]


def compare(components, variant="strict", **kw):
    orig = original_trace(components, variant,
                          kw.get("window_size", 0), kw.get("filter_window_size", 0))
    port = run_on_green_components(components, **kw)
    max_abs = {k: 0.0 for k in FIELDS}
    exact_rows = 0
    for o, p in zip(orig, port):
        row_exact = True
        for k in FIELDS:
            d = abs(o[k] - float(getattr(p, k)))
            max_abs[k] = max(max_abs[k], d)
            row_exact &= d == 0.0
        exact_rows += row_exact
    return {"frames": len(orig), "exact_rows": exact_rows, "max_abs_diff": max_abs, "original": orig, "port": port}


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "strict"
    b0, a0 = original_coeffs(variant)
    b1, a1 = butter((0.04, 0.2), 5)
    print(f"[{variant}] Butterworth b max|diff| = {max(abs(x - y) for x, y in zip(b0, b1)):.3g}, "
          f"a max|diff| = {max(abs(x - y) for x, y in zip(a0, a1)):.3g}")
    for bpm, seed in [(54, 3), (72, 1), (96, 2), (130, 4)]:
        comps = synthetic_ppg_green_components(bpm, 45, seed=seed)
        r = compare(comps, variant)
        last = r["port"][-1]
        print(f"[{variant}] SYNTHETIC {bpm} bpm: {r['exact_rows']}/{r['frames']} rows identical; "
              f"max|diff| bpm_average={r['max_abs_diff']['bpm_average']:.3g}; "
              f"final latest estimate port={last.bpm_latest:.2f} original={r['original'][-1]['bpm_latest']:.2f}")


if __name__ == "__main__":
    main()
