# Running and checking the updated component

Read README.md for scope and ALGORITHM.md for the recovered chain. Initialize original source with `git submodule update --init source` from the repository root before native builds or original-code comparisons. Run the remaining commands from `updated/`.

## Core and native filter

Native builds need CMake 3.20+ (for the documented CTest command), a C++17 compiler and its sanitizer runtime. Tested: Apple clang 16/macOS and GCC 11.4/Ubuntu 22.04.5.

The Python core requires Python 3.10+ with no third-party packages. Its existing `demo.py --csv samples.csv` reads one normalized green component per line at 30 Hz; it is legacy mode.

```python
from heartbeat_port.corrected import TimestampedHeartbeat
processor = TimestampedHeartbeat(max_gap_seconds=0.2)
result = processor.update(timestamp_seconds, normalized_green)
# result.bpm is None while warming up, on flat input, after a gap,
# without a recent peak, or outside the inherited 36–180 bpm clamp/passband range.
# Check result.status; no medical signal-quality claim is implied.
```

Times must be finite and strictly increasing; samples must lie in [0,1]. The wrapper linearly interpolates between consecutive samples; streaming use adds up to one input interval of latency. It does not open a camera. Flat gating requires a range below 1e-9 over the last 60 resampled values; maximum-gap default is 0.2 s. It requires 3 observed peaks and a peak in the preceding 2 s before exposing the inherited estimate; nonfinite values and rates outside 36–180 bpm are withheld. Status `warming_up` also covers stale/out-of-range estimates. Histories still grow with the supplied recording.

```sh
cmake -S native -B build/native -DHEARTBEAT_SANITIZE=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build build/native --parallel 2
ctest --test-dir build/native --output-on-failure
```

CMake builds only the repaired filter and its regression test on either platform. The full algorithm is built only by the macOS harness. See [native provenance and exact patch](native/PROVENANCE.md).

The following macOS-only harness commands require Apple clang/Foundation, using a new minimal UIKit shim:

```sh
python3 harness/compare_with_original.py strict
python3 harness/asan_check.py
python3 harness/build_repaired.py asan
```

`asan_check.py` intentionally reproduces failure in the original; do not treat it as a passing app build. New code does not alter the original source. The last command builds a repaired trace executable; invoke it as `build/heartbeat_trace_repaired_asan trace input.txt output.csv`. Input is one normalized component per line.

## Recorded-data replay

This replay uses the entire record 01. Download `bidmc_01_Signals.csv` and `bidmc_01_Numerics.csv` from the official [BIDMC v1.0.0 CSV directory](https://physionet.org/files/bidmc/1.0.0/bidmc_csv/), and retain [the dataset license](https://physionet.org/files/bidmc/1.0.0/LICENSE). The metrics JSON records their SHA-256 values, which were checked against the official SHA256SUMS.txt; see [the input-verification record](validation/2026-11-14/input-verification.json). Raw recordings are kept outside this repository.

Use a private virtual environment for optional replay/render dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip install numpy pillow matplotlib
.venv/bin/python tools/validate_recording.py --data /path/to/bidmc01 --out build/bidmc01
.venv/bin/python tools/render_recording.py --results build/bidmc01 --out build/media --frames build/frames
```

FFmpeg is also required for GIF/MP4 encoding. Tested rendering versions: NumPy 2.5.4, Pillow 13.0.0, Matplotlib 3.11.2 and FFmpeg 8.1.1 on macOS. Linux replay used NumPy 2.2.6/Python 3.10.12 and produced identical 1 Hz results.

Signals are pulse-oximeter PPG at 125 Hz, already within [0,1]; no amplitude normalization, inversion or reference-driven tuning is applied. Linear interpolation produces 14,401 samples at 30 Hz over 480 s. Metrics exclude 0–9 s and compare at each 1 Hz reference timestamp, without fitted lag. ECG-derived `HR` is the reference; PPG-derived `PULSE` is retained in the CSV for inspection but is not the scoring target. Coverage counts non-withheld estimates among 471 eligible reference samples. Reported MAE/RMSE are in bpm, not percent. No other subjects or held-out benchmark were evaluated.

Citation: Pimentel et al., *Towards a Robust Estimation of Respiratory Rate from Pulse Oximeters*, IEEE TBME 64(8), 1914–1923 (2016, as cited by the dataset); DOI 10.1109/TBME.2016.2613124. Dataset: Pimentel, Johnson, Charlton and Clifton, *BIDMC PPG and Respiration Dataset*, v1.0.0, PhysioNet. Data-derived traces/figures retain ODC Attribution 1.0 attribution; no new software license is inferred.

## Notebook and original app

The existing [notebook](notebooks/heartbeat_port_demo.ipynb) demonstrates the legacy synthetic component. All six code cells executed successfully in Jupyter on 2026-11-12; it was not changed or rerun for this revival. The new recorded-data validation is the command-line replay above.

A private `git archive` source copy was created from the unchanged pin, then `xcodebuild build` was attempted with Xcode 16.1/iOS 18.1 simulator, code signing disabled. Ambient C.UTF-8 first broke Xcode’s PNG helper; rerunning with `LC_ALL=C LANG=C` resolved that environmental issue and reached missing `FacebookSDK/FacebookSDK.h`. No full app/device run is claimed. The old finger/camera/flash/UI integrations were not replaced.

Platform citation requested by the current dataset page: Pollard et al., *PhysioNet as a global platform for biomedical research*, Nature Health 1, 792–795 (2026), [DOI 10.1038/s44360-026-00096-z](https://doi.org/10.1038/s44360-026-00096-z).
