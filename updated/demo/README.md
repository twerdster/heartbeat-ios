# Recorded PPG and saved-estimate replay

[Open the hosted demonstration](https://twerdster.github.io/heartbeat-ios/).

## Local use

From the repository root, use Python 3 and a browser:

```sh
python3 -m http.server --bind 127.0.0.1 --directory updated/demo
```

Open <http://127.0.0.1:8000/>. No dependency installation or build is required.

## Controls

Play/pause, seek through the eight-minute recording, change playback speed and inspect saved legacy, guarded and ECG reference values. The waveform window shows normalized resampled pulse-oximeter input.

## Verification and limitations

The browser page plays saved values; it does not run the estimator or use a camera. Dataset: BIDMC01, resampled to 30 Hz. The Python-derived 1 Hz estimates are copied from the dated validation CSV; their hashes are in [recording.json](recording.json). See [NOTICE.txt](NOTICE.txt) for attribution and ODC-By terms. The guarded wrapper had higher MAE on this single record (0.93 versus 0.76 bpm), so its presence is not a demonstrated accuracy improvement.

Actual Chrome checks on 2026-11-17 exercised the controls and 390-pixel/desktop layouts without JavaScript page errors or horizontal overflow. A narrow viewport is not a physical-device test; Safari/Firefox and physical phone input were not checked. Detailed current checks are in [VALIDATION.json](VALIDATION.json).

New demo source: Aaron Wetzler with agent assistance, 2026, under the scoped [MIT license](LICENSE). Original materials and supplied data retain their separate terms.
