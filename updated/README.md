# HeartBeat: updated algorithm port (2026)

This directory adds a modern, dependency-free port of the **signal-processing core** of the 2013 HeartBeat iPhone app
by Or Maayan and Michael Leybovich, supervised by Aaron Wetzler. It also adds a macOS harness that compiles and runs the
**unmodified original** algorithm code, so the two can be compared.

The original app in `../source/` (pinned upstream submodule `d5179096b96941bc0ff6aa8f0bacd88958dd37dd`) is
**not modified** and is **not** ported as an app. This is a student research prototype and **not a medical device**.

## Original vs updated

| | Original (`../source/Heartbeat/`) | Updated (`./`) |
|---|---|---|
| Platform | iOS 7 app (iPhone 5, camera and torch), Objective-C/C++, Core Plot, Facebook SDK | Python 3 standard library only; optional Apple clang harness |
| Input | Live 352x288 BGRA camera frames | Green components or BGRA buffers you pass in; synthetic generator included |
| Frame reduction | `UIImage+ImageAverageColor.m` `averageColorPrecise` | `heartbeat_port/frames.py` (same channel order; double-precision scale) |
| Filter | `Butterworth.cpp` (`butter`, `filter`) | `heartbeat_port/butterworth.py`: statement-for-statement port |
| Peak/BPM state machine | `Algorithm.mm` | `heartbeat_port/algorithm.py`: same constants, indices, smoothing and quirks |
| UI, audio, Facebook, results storage | Present | Not ported |

### Algorithm, as recovered from the code

1. Each frame is averaged over all pixels. The **green** component is used (`getColorValueFrom:` returns `green*255`), not red.
2. Once more than 60 frames exist (`filterWindowSize`), the latest 61 samples are mean-subtracted and filtered **from zero
   state** with an order-5 Butterworth band-pass at 0.04 to 0.2 of Nyquist (36 to 180 bpm at 30 fps).
3. The sample 10 frames back is a peak if it is greater than earlier neighbours and at least as great as later neighbours over 19 samples, with a 9-frame refractory period.
4. Peaks are counted over a 90-frame window, converted to bpm, clamped to [36, 180] and smoothed. Calibration uses a
   running weighted average; afterwards a 75-sample moving average is blended in.
5. `isFinalResultDetermined` and `shouldShowLatestResult` apply the original stability thresholds.

The app ran two instances, `algorithm` (window 9, filter window 60) and `algorithm2` (window 9, filter window 45).
Both configurations are tested.

### Deliberate deviations (documented in code)

* The original `filter()` loop runs to `i < np + 1`, so it **reads `x[np]` and writes `y[np]`, one past the arrays**
  allocated in `Algorithm.mm`. An AddressSanitizer build of the unmodified original reports
  `dynamic-stack-buffer-overflow ... Butterworth.cpp:220 in filter` (`harness/asan_check.py`). The port computes only
  the in-range outputs. The app never read the out-of-range element, so in-range results are unchanged.
* `ComputeNumCoeffs` uses a fixed `Numbers[11]` table, so orders above 5 overrun it. The port raises `ValueError` instead.
* `printf`/`NSLog` side effects, UIKit and memory leaks are not reproduced. `CGFloat` is a 64-bit double, as on 64-bit
  iOS. The 2013 iPhone 5 was 32-bit (`float` `CGFloat`), so last-digit differences against that device are possible.

* Frame averaging uses a double-precision scale instead of the original float32 expression. The reference harness starts from supplied green-component values; it does not verify bit-identical reduction of raw iPhone frames. Invalid dimensions, row strides and undersized buffers are rejected.

### Original quirks the port keeps on purpose (all confirmed against the compiled original)

* **A flat, pulseless input reports 72 bpm as a "final" result after 5 s.** `isCalibrationOver` does not require a
  detected peak, so the 72 bpm placeholder is returned. The app relied on a separate `red < 210` finger check.
* `isMissedPeak` reads the 72 bpm placeholder slot, not the latest estimate. After calibration a peak is therefore
  forced whenever 37.5 frames pass without one, whatever the measured rate.
* `int calibrationWeight = 2.5` truncates to 2. `shouldShowLatestResult` is sticky once true. `lastPeakPlace` is not
  updated for the first peak.

## Fidelity evidence

`harness/build_original.py` compiles the **unchanged** `Butterworth.cpp` and `Algorithm.mm` from `../source/Heartbeat/`.
It adds only `harness/uikit_shim.h`, a minimal `UIColor` interface, plus the new driver `harness/trace_main.mm`, and
links against Foundation. On the tested machine:

* Butterworth taps: **bit-identical** in the `-ffp-contract=off` build, and within 7.6e-14 in the default build, which may
  fuse multiply-adds. Matching required reproducing libc++'s `sqrt(complex(-1,0)) = (6.1e-17, 1)`.
* Per-frame traces (frame value, peak decision, instantaneous and averaged bpm, calibration/final/show/missed flags):
  **identical on every frame** for supplied green-component synthetic inputs tried (48 to 150 bpm, both app configurations, flat input), in both FP modes on the tested Mac. This does not establish raw-frame bit equivalence or Linux validation.
* `tests/fixtures/*_original_trace.csv` were produced by the compiled original (`harness/make_fixtures.py`). They let the
  tests check fidelity without a compiler.

## Commands (run from this `updated/` directory)

```sh
python3 -m unittest discover -s tests -v          # 20 tests; the live-harness test runs only on macOS + clang++
python3 demo.py                                   # synthetic 84 bpm timeline
python3 demo.py --bpm 110 --seconds 30 --svg build/demo.svg
python3 demo.py --csv my_mean_green_values.csv   # your own 30 fps mean-green series (0-255)
python3 harness/compare_with_original.py strict  # build + compare against the original code (macOS)
python3 harness/asan_check.py                    # confirm the original filter() overflow (macOS)
python3 tools/run_notebook.py notebooks/heartbeat_port_demo.ipynb --out build/heartbeat_port_demo.executed.ipynb
```

`notebooks/heartbeat_port_demo.ipynb` is committed clean, with no outputs. It also runs in Jupyter or Colab once the
repository is cloned. The stdlib runner validates the nbformat-4 structure and executes code cells in order. It is not a
Jupyter kernel. The notebook is also checked with nbformat and executed in an isolated real ipykernel during maintenance.

Tested 2026-11-12 on macOS 15 (Darwin 24.1, arm64), Python 3.14.4, Apple clang 16.0.0 (Xcode 16.1). No third-party
Python packages are used by the port. Notebook maintenance uses an isolated Jupyter environment. Linux has not been tested; its libm rounding can differ from the Mac-generated exact fixtures.

## What runs and what does not

* Runs: filter design, filtering, the complete peak/BPM state machine, frame averaging, demo, notebook and tests. The
  original algorithm code also runs on macOS through the harness.
* Does not run: the iOS app. It needs a physical iPhone with a torch, its iOS 7-era deployment target, Core Plot
  (`libCorePlot-CocoaTouch.a`) and a Facebook SDK framework at a developer-specific path that is absent. No Xcode
  build was attempted because there is no device or signing setup. Camera capture, audio and UI are not ported.
* No accuracy claim: every signal here is **synthetic** (`heartbeat_port/synthetic.py`). The waveform model is an
  assumption of this port, not data from the project. Agreement on synthetic signals says nothing about the
  measurements in the original report.

## Interactive potential

The port is pure Python with no I/O, so it could back a browser demo (Pyodide or a JS re-port) that takes a
webcam/fingertip mean-green series, or a small Hugging Face Space. Neither was created. Any public demo must keep the
"not a medical device" warning and explain the 72 bpm placeholder quirk.

## Licensing

No license file is added. The original source keeps its upstream copyright ("All rights reserved" headers), and no blanket license is granted for the derivative translation, original code or third-party material. Preserve the original authors' attribution and establish the applicable reuse terms with them. Original authors can request corrections or removal.
