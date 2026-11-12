#!/usr/bin/env python3
"""HeartBeat port demonstration (stdlib only).

Default: runs the ported original algorithm on a SYNTHETIC fingertip-like
signal and prints the estimate timeline. Optionally reads your own signal:

  python3 demo.py                       # synthetic 84 bpm, 45 s at 30 fps
  python3 demo.py --bpm 95 --seconds 40 --seed 3
  python3 demo.py --csv my_green.csv    # one mean-green value per line, 0-255, 30 fps
  python3 demo.py --svg out.svg         # also write a plot of signal, filter output and peaks

Synthetic results show the code path working. They are not a measurement of
the original app's accuracy. This is not a medical device.
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from heartbeat_port import HeartbeatAlgorithm  # noqa: E402
from heartbeat_port.butterworth import filter_original  # noqa: E402
from heartbeat_port.synthetic import synthetic_ppg_green_components  # noqa: E402


def write_svg(path: Path, alg: HeartbeatAlgorithm, fps: float, title: str) -> None:
    pts = alg.points
    n = len(pts)
    mean = sum(pts) / n
    filt = filter_original(10, alg.a, alg.b, [p - mean for p in pts])  # whole-signal view only
    W, H, pad = 900, 360, 40

    def poly(vals, top, height, colour):
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1.0
        coords = " ".join(f"{pad + (W - 2 * pad) * k / max(1, n - 1):.1f},"
                          f"{top + height - (v - lo) / span * height:.1f}" for k, v in enumerate(vals))
        return f'<polyline fill="none" stroke="{colour}" stroke-width="1.2" points="{coords}"/>'

    peaks = [i for i, p in enumerate(alg.is_peak) if p]
    marks = "".join(f'<line x1="{pad + (W - 2 * pad) * i / max(1, n - 1):.1f}" y1="190" '
                    f'x2="{pad + (W - 2 * pad) * i / max(1, n - 1):.1f}" y2="330" stroke="#c0392b" '
                    f'stroke-width="0.8" opacity="0.6"/>' for i in peaks)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="12">
<rect width="100%" height="100%" fill="white"/>
<text x="{pad}" y="20">{html.escape(title)}</text>
<text x="{pad}" y="40" fill="#555">mean green value (0-255)</text>
{poly(pts, 45, 120, "#2e7d32")}
<text x="{pad}" y="185" fill="#555">band-pass output (whole signal, illustration) and detected peaks (red)</text>
{poly(filt, 190, 140, "#1f4e79")}
{marks}
<text x="{pad}" y="{H - 8}" fill="#555">{n} frames at {fps:g} fps</text>
</svg>"""
    path.write_text(svg)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bpm", type=float, default=84.0,
                    help="rate of the SYNTHETIC signal (default avoids the original 72 bpm placeholder)")
    ap.add_argument("--seconds", type=float, default=45.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--csv", type=Path, help="mean-green values (0-255), one per line, 30 fps")
    ap.add_argument("--svg", type=Path, help="write an SVG plot here")
    args = ap.parse_args(argv)

    if args.csv:
        values = [float(x.split(",")[0]) for x in args.csv.read_text().splitlines()
                  if x.strip() and not x.startswith("#")]
        comps = [v / 255.0 for v in values]
        label = f"input file {args.csv.name}"
    else:
        comps = synthetic_ppg_green_components(args.bpm, args.seconds, seed=args.seed)
        label = f"SYNTHETIC signal at {args.bpm:g} bpm (seed {args.seed})"

    alg = HeartbeatAlgorithm()
    print(f"# {label}; original parameters: 30 fps, window 9, filter window 60, calibration 90")
    print("time_s  latest_bpm  calibration_over  final_determined  should_show")
    for k, c in enumerate(comps, start=1):
        alg.new_frame_with_green_component(c)
        final = alg.is_final_result_determined()
        show = alg.should_show_latest_result()
        if k % 75 == 0 or k == len(comps):
            print(f"{k / 30:6.1f}  {alg.bpm_latest_result:10.2f}  {int(alg.is_calibration_over):16d}  "
                  f"{int(final):16d}  {int(show):11d}")
    peaks = sum(alg.is_peak)
    print(f"# detected peaks: {peaks}; final latest estimate: {alg.bpm_latest_result:.2f} bpm")
    if args.svg:
        write_svg(args.svg, alg, 30.0, label)
        print(f"# wrote {args.svg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
