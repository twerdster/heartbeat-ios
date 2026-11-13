# HeartBeat algorithm and reference comparison

These notes describe the legacy Python signal-processing component and its comparison with pinned original source `d5179096b96941bc0ff6aa8f0bacd88958dd37dd`. The 2026-11-12 comparisons used synthetic green-channel sequences. The separately recorded 2026-11-14 work adds a repaired native filter, an optional guarded Python wrapper and one public pulse-oximeter PPG replay; see [the running guide](RUNNING_2026.md). None of these runs evaluates the iPhone camera application or reproduces its original report measurements.

## Processing chain

1. Each frame is averaged over all pixels. The **green** component is used (`getColorValueFrom:` returns `green*255`), not red.
2. For the `algorithm` configuration, once more than 60 frames exist (`filterWindowSize`), the latest 61 samples are mean-subtracted and filtered **from zero
   state** with an order-5 Butterworth band-pass at 0.04 to 0.2 of Nyquist (36 to 180 bpm at 30 fps).
3. The sample 10 frames back is a peak if it is greater than earlier neighbours and at least as great as later neighbours over 19 samples, with a 9-frame refractory period.
4. Peaks are counted over a 90-frame window, converted to bpm, clamped to [36, 180] and smoothed. Calibration uses a
   running weighted average; afterwards a 75-sample moving average is blended in.
5. `isFinalResultDetermined` and `shouldShowLatestResult` apply the original stability thresholds.

`algorithm2` uses a 45-frame filter-window setting and therefore filters the latest 46 samples; the remaining chain is the same.

The app ran two instances, `algorithm` (window 9, filter window 60) and `algorithm2` (window 9, filter window 45).
The recorded tests cover both configurations on selected synthetic inputs.

## Deliberate deviations

* The original `filter()` loop runs to `i < np + 1`, so it **reads `x[np]` and writes `y[np]`, one past the arrays**
  allocated in `Algorithm.mm`. An AddressSanitizer build of the unmodified original reports
  `dynamic-stack-buffer-overflow ... Butterworth.cpp:220 in filter` (`harness/asan_check.py`). The port computes only
  the in-range outputs. The original caller reads only the in-range elements. Recorded comparisons match those outputs; the port does not reproduce the undefined extra read/write.
* `ComputeNumCoeffs` uses a fixed `Numbers[11]` table, so orders above 5 overrun it. The port raises `ValueError` instead.
* `printf`/`NSLog` side effects, UIKit and memory leaks are not reproduced. `CGFloat` is a 64-bit double, as on 64-bit
  iOS. The 2013 iPhone 5 was 32-bit (`float` `CGFloat`), so last-digit differences against that device are possible.

* Frame averaging uses a double-precision scale instead of the original float32 expression. The reference harness starts from supplied green-component values; it does not verify bit-identical reduction of raw iPhone frames. Invalid dimensions, row strides and undersized buffers are rejected.

## Retained historical behavior

These quirks remain in `HeartbeatAlgorithm` for comparison. The optional `TimestampedHeartbeat` API changes the flat-input and forced-missed-peak behavior; its output is separately labeled.

* **A flat synthetic input reports 72 bpm as a "final" result after about 5 s at 30 fps.** `isCalibrationOver` does not require a
  detected peak, so the 72 bpm placeholder is returned. The app relied on a separate `red < 210` finger check.
* `isMissedPeak` reads the 72 bpm placeholder slot, not the latest estimate. After calibration a peak is therefore
  forced whenever 37.5 frames pass without one, whatever the measured rate.
* `int calibrationWeight = 2.5` truncates to 2. `shouldShowLatestResult` is sticky once true. `lastPeakPlace` is not
  updated for the first peak.

## Comparison evidence

`harness/build_original.py` compiles the **unchanged** `Butterworth.cpp` and `Algorithm.mm` from `../source/Heartbeat/`.
It adds only `harness/uikit_shim.h`, a minimal `UIColor` interface, plus the new driver `harness/trace_main.mm`, and
links against Foundation.

The saved 2026-11-12 test log records all 20 tests passed, including the live compiled-original test. That test uses the `strict` build (`-ffp-contract=off`) and selected synthetic 48/150 bpm sequences plus flat input. It requires exact equality of every recorded per-frame field. Separate saved-fixture tests require exact field equality for the `algorithm` app configuration (synthetic 72 bpm) and `algorithm2` (synthetic 110 bpm), and exact coefficient equality against the saved strict-build fixture.

`tests/fixtures/*_original_trace.csv` and `original_butter_coeffs.csv` were produced by the compiled original through `harness/make_fixtures.py`. They permit fixture comparisons without a compiler. The harness also exposes a `default` floating-point build, but the strict-build test result does not establish all compiler modes or platforms. No comparison here covers raw camera-frame reduction, historical 32-bit device arithmetic or pulse-rate accuracy on people.

## Separately repaired filter and guarded replay (2026-11-14)

The [native filter copy and patch](native/PROVENANCE.md) change only bounds in `filter()`. Its coefficients and the original `Algorithm.mm` remain unchanged. The repaired macOS harness agrees exactly with the legacy Python port in all 11 trace fields for 14,401 resampled BIDMC01 frames and two 900-frame synthetic sequences covering both original window configurations. The standalone filter's 14-case direct-recurrence test (seven lengths, transfer orders 2 and 10) passes ASan/UBSan on Mac and Linux; the full Objective-C++ harness is Mac-only.

`CorrectedHeartbeatAlgorithm` disables the historical forced-peak branch and requires an observed first peak before calibration. `TimestampedHeartbeat` adds finite/range checks, offline 30 Hz linear resampling, gap resets and withholding when the range of the last 60 resampled frames (~2 s) is below 1e-9. These gates are not a general signal-quality or finger detector. The real recording comparison uses the inherited filter/peak/count/smoothing chain; the guarded mode’s combined changes had higher rate error on that record. Current metrics, coverage, reference selection and limitations are recorded in [the validation evidence](validation/2026-11-14/).
