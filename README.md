# HeartBeat for iOS

<p align="center">
  <img src="assets/project-preview.jpg" alt="Two Hebrew-language HeartBeat app screens: a measurement screen showing 59 with a pulse waveform, and a results list of timestamped beats-per-minute readings" width="440">
</p>

![Platform: iOS (iPhone)](https://img.shields.io/badge/platform-iOS%20%28iPhone%29-lightgrey)
![Code: Objective-C / Objective-C++](https://img.shields.io/badge/code-Objective--C%20%2F%20Objective--C%2B%2B-blue)
![Source: pinned upstream submodule](https://img.shields.io/badge/source-pinned%20upstream%20submodule-blue)

Heart-rate measurement using an iPhone camera and flash to record color changes in illuminated skin; the original implementation analyzes the green color plane.

Students: Or Mayaan, Michael Leybovich.

Supervision: Aaron Wetzler.

## Status

The [original ten-page final report](docs/report.pdf) has been recovered. The original students' [Heartbeat repository](https://github.com/mishana/Heartbeat) is included as the `source/` Git submodule, pinned to `d5179096b96941bc0ff6aa8f0bacd88958dd37dd`. This is historical source, not a tested modern iOS release.

## Original code

[`source/`](https://github.com/mishana/Heartbeat/tree/d5179096b96941bc0ff6aa8f0bacd88958dd37dd) is a Git submodule pointing to the students' [mishana/Heartbeat](https://github.com/mishana/Heartbeat) repository at commit `d5179096b96941bc0ff6aa8f0bacd88958dd37dd`. Its contents, including the original copyright notice, are the upstream's own files, unmodified by this archive. Clone with `--recurse-submodules` to populate it. The signal-processing logic is in `source/Heartbeat/Algorithm.mm` and `source/Heartbeat/Butterworth.cpp`.

## Running

```sh
git clone --recurse-submodules https://github.com/twerdster/heartbeat-ios.git
cd heartbeat-ios
open source/Heartbeat.xcodeproj
```

Use Xcode to inspect the historical `Heartbeat` target. The report documents an iPhone 5 running iOS 7, with Apple camera/graphics/audio frameworks, Core Plot and the Facebook SDK. The Xcode project targets iOS 7.0 for the app and contains a developer-relative Facebook SDK framework path that must be replaced with a compatible, properly licensed local dependency. Camera/flash operation requires a physical device; use your own signing configuration, not recovered provisioning material. The original implementation analyzes the green color plane and applies a Butterworth band-pass filter.

These are historical requirements, not a verified modern dependency list. Original source was inspected but not compiled or run; obsolete APIs and dependencies may require porting. The pinned upstream retains its original copyright and all-rights-reserved notice; no new license is assigned here. This student research prototype is not a medical device.

## Links

- [Project entry on Aaron Wetzler's website](https://twerdster.github.io/#heartbeat-for-ios)
- [Original final report](docs/report.pdf)
- [Original demonstration](https://www.youtube.com/watch?v=dHomdiuAAFw)

## Attribution and Updates

Original student and third-party attribution will be retained. No license for unrecovered source code is implied by this README. Original authors can open an issue to contribute updates or request corrections or removal of their material.

Figure provenance: `assets/project-preview.jpg` is the original student-project app screenshot figure from the archived project page on Aaron Wetzler's website, copied without modification. The readings shown are historical app output, not validated measurements.

