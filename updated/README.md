# HeartBeat signal-processing component (updated 2026)

This Python translation implements the filter and peak/BPM state machine from the HeartBeat iOS prototype by Or Maayan and Michael Leybovich, supervised by Aaron Wetzler. The original app remains unchanged in the pinned `../source/` submodule. Camera capture, finger-presence checks, UI, audio, Facebook integration and result storage are not ported.

## Inputs and outputs

`HeartbeatAlgorithm` accepts green components normalized to `[0, 1]`, or mean-green values on `[0, 255]` through its convenience method. The original constants assume 30 frames per second. `frames.py` can reduce a supplied BGRA buffer to RGB channel means, with explicit dimensions and row stride. It does not open a camera.

Processing subtracts each window's mean, applies an order-5 Butterworth band-pass, detects local peaks, counts them over a 90-frame window, then clamps/smooths the estimate. The 0.04–0.2 Nyquist band corresponds to 36–180 beats per minute at 30 fps. The API exposes estimates and calibration/final/display flags; the demo prints a time series in seconds and bpm.

## Setup and use

The Python component requires Python 3.10+ and the standard library. Run from this directory:

```sh
python3 demo.py --bpm 84 --seconds 30
python3 demo.py --csv my_mean_green_values.csv
python3 -m unittest discover -s tests -v
```

CSV input is one mean-green value per line (the first comma-separated field is read), sampled at 30 fps. This exercises the core without the original app's finger-presence check. For SVG output, create an output directory first:

```sh
mkdir -p build
python3 demo.py --bpm 110 --seconds 30 --svg build/demo.svg
```

The synthetic input has a chosen pulse rate; it is a generated example, not a measured pulse or trained model. The SVG's whole-signal filter plot is illustrative: the state machine itself re-filters short windows from zero state.

## Notebook and reference commands

Open [the notebook](notebooks/heartbeat_port_demo.ipynb) in Jupyter after cloning the repository. The port has no package dependencies; a real notebook session needs a Jupyter kernel installed separately. Its six code cells are checked in without outputs. The supplied ordered-cell runner is a smoke check, not a Jupyter kernel or sandbox:

```sh
python3 tools/run_notebook.py notebooks/heartbeat_port_demo.ipynb --out build/heartbeat_port_demo.executed.ipynb
```

To compare against original source, initialize the submodule from the repository root. The live harness requires macOS Foundation and Apple clang:

```sh
python3 harness/compare_with_original.py strict
python3 harness/asan_check.py
```

The second command intentionally checks for an overflow in the original filter; it is not a port failure. The harness compiles unchanged `Algorithm.mm`/`Butterworth.cpp` with a minimal UIKit interface. See [algorithm and comparison notes](ALGORITHM.md) for the operator chain, floating-point modes and retained quirks.

## Recorded validation and limits

[VALIDATION.json](VALIDATION.json) records 20 component unit tests and six real Jupyter code cells passed on 2026-11-12, using macOS 15.1.1 arm64, Python 3.14.4 and Apple clang 16.0.0. The tests cover filter coefficients/output, frame reduction, algorithm state, saved original traces and a live harness comparison. The saved run log marks that live comparison as passed among all 20 tests. The live-harness test requires macOS/clang and skips when that toolchain is unavailable. With it present, missing original files from an uninitialized submodule cause a failure rather than a skip. A test run that skips this case does not establish that comparison again.

Every per-frame field in the supplied synthetic green-component traces matches the compiled original exactly on the tested Mac for both historical app configurations. Raw-frame reduction is not bit-identical: Python uses double-precision scaling where the original uses float32. The original iPhone 5 also used 32-bit `CGFloat`, unlike the comparison harness. Linux execution and rounding have not been validated.

The port avoids the original filter's out-of-bounds final write and rejects unsupported filter orders. It deliberately retains output quirks, including a flat signal returning the 72 bpm placeholder and missed-peak logic consulting that value. These behaviors make an apparently stable estimate insufficient evidence of a pulse. No original app build, device accuracy, clinical accuracy or benchmark is established. This research software is not a medical device.

## Attribution and terms

Claude Code drafted the translation; Codex completed/reviewed/tested it for Aaron Wetzler in 2026. Original files retain their upstream all-rights-reserved notices. No blanket license is assigned to original or derived work. Preserve the original authors' attribution and establish applicable reuse terms with them; authors can request corrections or removal.
