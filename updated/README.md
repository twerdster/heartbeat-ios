# Heartbeat processing core — updated 2026

![Recorded pulse replay](assets/heartbeat-recording.gif)

Recorded BIDMC01 pulse-oximeter PPG with legacy/guarded estimates and recorded ECG-derived heart rate. The six-second animation replays a 60-second excerpt at 10×; metrics cover the full eight-minute recording after a ten-second warm-up. [MP4](assets/heartbeat-recording.mp4) · [Full-size plot](assets/heartbeat-recording.png).

This component runs the green-channel filter, peak detection and BPM state machine recovered from Or Maayan and Michael Leybovich’s HeartBeat app, supervised by Aaron Wetzler. It accepts supplied samples; camera capture, finger detection, UI, Facebook integration and storage remain outside this component. The original pinned `../source/` is unchanged.

## What works and what changed

The existing standard-library Python translation remains the legacy mode. A separately repaired C++ filter now bounds its startup and final loops. It is substituted into unchanged `Algorithm.mm` in a macOS harness with a minimal UIKit shim; the filter alone also builds on Linux. The Butterworth coefficients, local-peak/count/smoothing chain and original 61/46-sample window configurations remain intact.

An optional Python `TimestampedHeartbeat` wrapper does not insert inferred missed peaks, requires observed peaks before calibration, withholds constant input and resets after gaps. It resamples supplied timestamps onto the original 30 Hz grid. These are labeled behavioral changes, not recovered app behavior; they do not classify every noisy or finger-free input.

## Run

Python 3.10+ is sufficient for the core and component tests:

```sh
python3 demo.py --bpm 84 --seconds 30
python3 -m unittest discover -s tests -v
```

The demo input is synthetic. `HeartbeatAlgorithm` still exposes historical placeholder/display quirks for comparison. For the guarded API, build commands, real-data replay and notebook, see [the running guide](RUNNING_2026.md). The [algorithm notes](ALGORITHM.md) describe the operator chain and floating-point qualifications.

## Verified results

On 2026-11-14, 25 Python tests passed on macOS; Linux passed 24 with the macOS Foundation comparison explicitly skipped. The repaired C++ filter’s independent recurrence test (seven lengths each, transfer orders 2 and 10) passed with AddressSanitizer/UndefinedBehaviorSanitizer on both systems. On macOS, ASan reproduced the original filter overflow; the repaired build completed the same 90-frame input without an ASan report (no leak check).

On macOS, the repaired native algorithm and legacy Python agree in all 11 trace fields for 14,401 BIDMC01 frames and two 900-frame synthetic configurations. Against 471 ECG-derived HR samples (1 Hz, 10–480 s), legacy mode had MAE 0.76 bpm/RMSE 1.19 bpm; guarded mode had higher error, MAE 0.93 bpm/RMSE 1.50 bpm. Guarded mode returned an estimate at all 471 timestamps; legacy mode does not withhold by design. [Metrics, traces and logs](validation/2026-11-14/).

## Limits and attribution

The attempted Xcode 16.1/iOS 18.1 simulator build (signing disabled, locale C) stopped at missing `FacebookSDK/FacebookSDK.h`; later blockers remain unknown. No device/camera, historical 32-bit arithmetic, clinical accuracy, multi-subject benchmark or full iOS application validation is established. BIDMC is pulse-oximeter PPG, not camera data; results from one record do not establish general performance. The inherited long-term smoothing can obscure short rate changes.

Claude Code drafted the earlier translation; Codex completed/tested it and prepared the separately labeled 2026-11-14 repairs, guards and replay tooling for maintainer Aaron Wetzler. Original source notices and student credits remain. No blanket code license is added. BIDMC data/figures are attributed to Pimentel and colleagues, PhysioNet v1.0.0, under [ODC Attribution 1.0](https://physionet.org/content/bidmc/1.0.0/).
