# heartbeat-ios: maintenance context

Read SUMMARY.md, then SKILL.md, the reference README and updated documentation. Current results: 2026-11-14.

## Updated-work navigation (2026-11-14)

Aaron authorized a top-of-page `New!` badge and “Updated and ported for modern hardware” link in the root README. Both lead to the corresponding heading in `updated/README.md`, which now opens with a brief description of the actual port, repairs or reimplementation and its limits. An italic line marks the following content as the historical reference. The historical root reference body remains unchanged; current implementation details stay under `updated/`.

This documentation change does not alter source, submodule pins, media or recorded validation. Earlier root-README byte-identity statements and hashes apply to their recorded baseline; current preservation checks remove only the authorized navigation block before comparing the historical body.

## Purpose and preservation

HeartBeat is an iPhone green-channel pulse-estimation prototype by Or Maayan and Michael Leybovich, supervised by Aaron Wetzler. The source submodule remains unchanged at d5179096b96941bc0ff6aa8f0bacd88958dd37dd. Preserve original files, notices and author attribution. The root README is the project reference; new work belongs under updated/.

## Current executable work

The existing legacy Python translation remains available. A separate native Butterworth copy fixes filter loop bounds; the macOS harness substitutes it into unchanged Algorithm.mm with a UIKit shim. The earlier `updated/native/` CMake project builds only the repaired filter and recurrence driver on Mac/Linux. The optional Python wrapper withholds near-flat input, requires observed peaks, disables inferred missed-peak insertion and handles timestamps/gaps. Interpolation needs consecutive samples; streaming use adds up to one input interval of latency. Range/stale gates can also withhold results. It is not a camera or general signal-quality classifier.

Mac: 25 Python tests passed. Linux: 24 passed and the Mac/Foundation comparison skipped. One CTest covers 14 recurrence cases (transfer orders 2/10, seven lengths each), with ASan/UBSan on both platforms. On Mac, the original filter aborts under ASan; the repaired build completes the same 90-frame input. The repaired macOS harness matches the legacy Python output in all 11 trace fields for 14,401 BIDMC01 frames and two 900-frame synthetic configurations.

The eight-minute BIDMC01 pulse-oximeter recording is not camera data. Against 471 ECG-derived 1 Hz HR samples at 10–480 s, legacy MAE is 0.7623 bpm and guarded MAE 0.9341 bpm. Guarded mode has higher error here and returns estimates at every eligible timestamp; legacy never withholds by design. Linux/Mac 1 Hz output CSVs are byte-identical. No other records or clinical/device accuracy were evaluated.

An `xcodebuild build` of a private git-archive copy of the unchanged app source attempted with Xcode 16.1/iOS 18.1 simulator first hit an ambient locale/copypng failure. Locale C resolved that; compilation then stopped at missing FacebookSDK headers. Later blockers are unknown. Full app/camera/flash/UI and historical 32-bit behavior remain unvalidated; inherited smoothing and raw-frame precision qualifications remain.

## Workflow and evidence

See updated/README.md and updated/RUNNING_2026.md for commands and dependencies. updated/VALIDATION.json retains current checks plus the dated earlier notebook record; updated/validation/2026-11-14/ contains metrics, traces, hashes and logs. The six notebook code cells executed in Jupyter on 2026-11-12 were not rerun here.

Media live under updated/assets/. Preserve GIF <2,000,000 bytes and MP4 <10,000,000 bytes; playback rate is not execution throughput. Bulk data and intermediates use the verified AgentSSD task directory recorded in the private handoff. Recheck SSD mount identity/free space/write access before large writes; keep builds/environments on native filesystems. Private host/build paths and full logs are recorded in the task handoff.

On 2026-11-12 Michael Leybovich confirmed he was comfortable with Aaron keeping the archival page/repository. This records his response only; preserve correspondence privately and existing code/third-party terms. No blanket license is added. BIDMC-derived results retain the dataset attribution/license.

Earlier documentation received Claude reviews on 2026-11-12 and 2026-11-13. Two tools-disabled Claude editorial reviews also completed on 2026-11-14; useful corrections were checked against code/results and applied. Before every commit reread/synchronize SUMMARY.md and SKILL.md, verify source hashes/pin and root README identity, and check changed links/media/diff scope. No package bundles these docs.

## New native replay interfaces, 2026-11-14

New code under `updated/platforms/` translates the recovered state machine to C++17, uses the separately bounded native filter and verified saved coefficients, and adds UIKit, Android Canvas/JNI, AppKit and Linux Tk frontends. These process bundled BIDMC01 PPG (14,401 samples at 30 Hz, nominal 6× replay) or a labeled synthetic 84 bpm signal. They do not restore the historical camera app or its UI. See `updated/platforms/NATIVE.md` for setup, controls, output paths and qualifications.

Actual replays completed on iPhone 12/iOS 18.0.1, Pixel 2/Android 10, Apple Silicon/macOS 15.1.1 and x86_64/Ubuntu 22.04. Each finished the eight-minute input with an estimate of 90.8614681142 bpm. Linux uses an isolated Xvfb display. The separate C++ CLI matched all 11 Python trace fields for 14,401 BIDMC01 frames and two 900-frame synthetic fixtures on macOS; the same comparison passed under macOS ASan/UBSan. Linux CLI parity also passed with ASan, UBSan and leak detection enabled. Final capture and artifact records are in `updated/validation/native-platforms/`. These counts describe translation parity, not independent accuracy tests.

New native UI recordings are separate from the earlier generated comparison figure. Keep the original source pin and root reference README unchanged. GIFs must remain below 2 MB and MP4s below 10 MB. Build tools and environments use a native filesystem; bulk captures use the verified AgentSSD task directory recorded in the private handoff. No signing identities, device identifiers or private host paths belong in the repository.

Final native recordings and completed-only result files are present for all four platforms. The final Android APK and Apple binaries are bound to hashes in `updated/validation/native-platforms/`. Input/output helpers have 26 plain-JVM checks and 28 Linux callback/filesystem checks, including a full core replay during blocked writes and save recovery. An actual AppKit synthetic run completed during a blocked output directory, showed the error, and saved automatically after restoration; the previous BIDMC completion record survived. Focused tools-disabled Claude reviews of the final Apple save logic and Android/Linux helpers completed with no verified material issues. Minor Apple pause/invalid-input screen-awake limits remain documented in NATIVE.md. These checks add no camera or clinical validation.
