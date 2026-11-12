#!/usr/bin/env python3
"""Regenerate tests/fixtures/* from the compiled ORIGINAL code (strict FP build).

The fixtures let the Python tests check the port against outputs of the
original code on machines without a compiler. Inputs are SYNTHETIC.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from compare_with_original import original_coeffs, original_trace  # noqa: E402
from heartbeat_port.synthetic import synthetic_ppg_green_components  # noqa: E402

FIX = HERE.parent / "tests" / "fixtures"


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    b, a = original_coeffs("strict")
    with (FIX / "original_butter_coeffs.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(["k", "b", "a"])
        for k, (bk, ak) in enumerate(zip(b, a)):
            w.writerow([k, repr(bk), repr(ak)])
    cases = [("synthetic_72bpm_seed1", 72, 1, 0, 0), ("synthetic_110bpm_seed7_alg2", 110, 7, 9, 45)]
    for name, bpm, seed, w_, fw in cases:
        comps = synthetic_ppg_green_components(bpm, 40, seed=seed)
        (FIX / f"{name}_input.txt").write_text(
            "# SYNTHETIC green components (heartbeat_port.synthetic), not a recording\n"
            + "".join(f"{c!r}\n" for c in comps))
        rows = original_trace(comps, "strict", w_, fw)
        with (FIX / f"{name}_original_trace.csv").open("w", newline="") as f:
            wr = csv.writer(f, lineterminator='\n')
            wr.writerow(list(rows[0].keys()))
            for r in rows:
                wr.writerow([repr(v) for v in r.values()])
    print("fixtures written to", FIX)


if __name__ == "__main__":
    main()
