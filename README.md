# HeartBeat for iOS

Heart-rate measurement using an iPhone camera and flash to record changes in the red-channel reflectance of illuminated skin.

Students: Or Mayaan, Michael Leybovich.

Supervision: Aaron Wetzler.

## Status

The [original ten-page final report](docs/report.pdf) has been recovered. The original students' [Heartbeat repository](https://github.com/mishana/Heartbeat) is included as the `source/` Git submodule, pinned to `d5179096b96941bc0ff6aa8f0bacd88958dd37dd`. This is historical source, not a tested modern iOS release.

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

