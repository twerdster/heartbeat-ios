# Native replay interfaces

These 2026 interfaces process supplied samples through the recovered estimator. The original iOS app supplied a normalized green-channel value at this boundary; the new replay uses PPG or synthetic samples. They are new frontends around a C++ translation of the recovered `Algorithm.mm` state machine and the separately repaired native Butterworth filter. The historical app and its camera, finger-presence check and Facebook integration are not restored by these frontends. Original files remain in `../../source/`.

## Input and execution

The bundled `data/bidmc01-ppg.csv` contains 14,401 PPG samples in the supplied 0–1 range resampled from the public eight-minute BIDMC01 recording to 30 Hz. It is pulse-oximeter data, not camera data. The default replay computes six samples per display tick; the 6× label describes input playback, not measured throughput. “Switch input” selects a labeled 30-second synthetic waveform at 84 bpm. Pause holds processing and Restart creates a fresh estimator.

Every displayed estimate is computed by the running native core. There are no saved estimates or result movies in the app bundles. The waveform shows the most recent eight seconds of supplied input with a changing vertical scale. The core retains the original peak counting, long smoothing, 72 bpm placeholders and missed-peak behavior. The new interfaces show “—” until calibration completes, then display the latest estimate; they do not reproduce the historical `shouldShowLatestResult` or `isFinalResultDetermined` display gates. The optional Python guard layer is not enabled in these apps.

The portable coefficients are the saved order-10 transfer coefficients for the original order-5 bandpass. They match the original generator fixture. Floating-point contraction is disabled for parity checks. This preserves the evaluated 64-bit behavior; it does not establish historical 32-bit iPhone arithmetic.

## Build and run

Initialize the source submodule first. CMake 3.20+ and a C++17 compiler build the shared library and CLI:

```sh
cmake -S platforms -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native -j4
python3 platforms/verify_portable.py build/native/heartbeat_cli
```

Run from `updated/`. The verification script compares all 11 trace fields against the earlier faithful Python translation for BIDMC01 and two 900-frame synthetic configurations (filter windows 60 and 45). It checks parity, including known quirks; it is not an independent accuracy benchmark. Set `-DHEARTBEAT_NATIVE_SANITIZE=ON` for address/undefined-behavior checks of the library and CLI. The configuration stops on sanitizer errors; the recorded Linux check also enabled leak detection.

On macOS, the same build creates `build/native/HeartbeatUpdated.app`, an AppKit window. On Linux, install Python 3.10+ with Tk and run the new Tk interface against the compiled shared library:

```sh
python3 platforms/linux_ui.py --library build/native/libheartbeat_core.so \
  --output build/native/linux-state.json
```

The tested Ubuntu host used user-local Tk packages and an isolated Xvfb display for the screen capture. That recording shows execution on the Linux machine with a virtual display; it is not a physical-monitor capture.

For iOS, Xcode 16.1 and the iOS 18.1 SDK built a UIKit application for arm64, deployment target 16.0:

```sh
cmake -G Xcode -S platforms -B build/ios -DCMAKE_SYSTEM_NAME=iOS \
  -DCMAKE_OSX_SYSROOT=iphoneos -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=16.0 \
  -DHEARTBEAT_BUNDLE_ID=YOUR_REGISTERED_BUNDLE_ID \
  -DCMAKE_XCODE_ATTRIBUTE_DEVELOPMENT_TEAM=YOUR_TEAM
xcodebuild -project build/ios/heartbeat_native.xcodeproj -target HeartbeatUpdated \
  -configuration Release -sdk iphoneos -allowProvisioningUpdates build
```

Use your own signing team and device. No signing credentials or device identifiers are stored in the repository. The tested bundle ID is `io.github.twerdster.heartbeat.updated`; choose one registered to your own team with `HEARTBEAT_BUNDLE_ID`. The iPhone target was tested only at the iPhone 12 layout size. Other phone sizes and VoiceOver have not been validated.

For Android, use JDK 17 or 21, Gradle 8.7, SDK/build-tools 34, NDK 27.2.12479018 and CMake 3.22.1. The Java Canvas interface calls the same C++ core through JNI. It targets SDK 34, requires API 26+, and currently builds arm64:

```sh
gradle -p platforms/android assembleDebug
adb install -r platforms/android/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n org.awetzler.heartbeat.updated/.MainActivity
```

Gradle is not bundled; `ANDROID_HOME` must point to the installed SDK. App bundles include the input CSV and data notice. They do not need a network connection, camera permission or a host server.

## Recorded checks and limitations

See [native platform evidence](../validation/native-platforms/) for per-platform result files, parity checks and capture provenance. The eight-minute replay completed on an iPhone 12/iOS 18.0.1, Pixel 2/Android 10, Apple Silicon/macOS 15.1.1 and x86_64/Ubuntu 22.04. Their final estimate was 90.8614681142 bpm. Matching this single terminal value is a completion check; the separate desktop CLI comparisons cover all trace fields.

UIKit writes container-relative `Documents/HeartbeatNative/native-state.json`; AppKit writes `~/Library/Application Support/HeartbeatNative/native-state.json`; Android writes its private `files/native-state.json`; Linux uses the specified output path. The files record input, frame count, completion, replay rate and latest estimate. Each frontend saves latest progress snapshots plus per-input `*-complete.json` files written only at completion. A partial restart or a different input leaves the last completed record intact; another completed run may replace it. On Linux, choose an output path distinct from these reserved completion filenames. Before calibration, `bpm` is null. The replay rate field is nominal. These are replay outputs, not new measurements from a sensor.

The save checks cover 26 plain-JVM input/filesystem assertions for the Android helper, 28 Linux callback/filesystem assertions using the actual core and fake widgets, and one actual AppKit blocked-directory/recovery run. The first two are separate from the physical phone and real GUI captures. Save failures remain visible; a completed, unpaused replay retries once per second. Individual JSON files are replaced atomically, rather than as a cross-file transaction. These checks do not cover process death or power loss. Reproduce the helper checks with [the test guide](tests/README.md).

The final static review left two minor Apple UI limits: Pause can change the status of an already completed replay, and missing bundled input can leave the iPhone screen awake. The supplied input passed validation in the recorded builds. A paused replay requires Resume before a failed completion save can retry.

A successful replay does not validate live camera acquisition, clinical accuracy, arbitrary signal quality or performance across devices. The [earlier validation](../validation/2026-11-14/) reports error against recorded ECG-derived HR and the guarded mode's higher error on this record. Keep those accuracy results separate from platform execution evidence.

## Attribution

Original HeartBeat authors: Or Maayan and Michael Leybovich; supervisor/maintainer: Aaron Wetzler. The new frontends and portable translation are labeled 2026 work. Original notices and code terms remain unchanged; no blanket license is added.

The bundled CSV is derived from BIDMC PPG and Respiration Dataset 1.0.0 by Pimentel and colleagues, hosted by PhysioNet, under [ODC Attribution 1.0](https://physionet.org/content/bidmc/1.0.0/). Raw input hashes, citation and resampling scope are retained in the earlier [input verification](../validation/2026-11-14/input-verification.json). The bundled derived CSV has its own SHA-256 in native validation. The data notice travels in app resources and Android assets (`data/NOTICE.txt` in source, packaged as `NOTICE.txt` at the asset/resource root), and the UI includes the dataset attribution. It is public research data, not a recording from the test phones.
