# Native replay IO checks

Build the shared core as described in [NATIVE.md](../NATIVE.md), then run these commands from `updated/`.

```sh
python3 platforms/tests/test_linux_io.py --library build/native/libheartbeat_core.so \
  --result validation/native-platforms/linux-io-tests.json

mkdir -p build/io-java
javac -d build/io-java \
  platforms/android/app/src/main/java/org/awetzler/heartbeat/updated/ReplayFiles.java \
  platforms/android/tests/ReplayFilesTest.java
java -cp build/io-java org.awetzler.heartbeat.updated.ReplayFilesTest
```

Python 3.10+ and the compiled Linux shared library are required for the first command; no Tk installation or display is needed. JDK 17 or 21 runs the second check without an Android SDK or device.

The [Linux regression](test_linux_io.py) passed 28 assertions on Ubuntu 22.04. It checks the `sample` CSV header, nonempty input, finite values in 0–1, atomic replacement failure, existing-file preservation, temporary-file cleanup and preservation of a completed input during later partial saves. It also drives the actual Tk callback code with fake widgets and a fake clock while the unchanged C++ core processes all 14,401 bundled BIDMC01 samples through ctypes. A blocked output path leaves a visible error while processing completes; making it writable allows the completion retry to save. The terminal estimate remains 90.86146811423824 bpm. This is callback/IO integration, not a real GUI recording or an accuracy evaluation. The fixture and final-value assertion are specific to the bundled BIDMC01 input.

The [Java helper check](../android/tests/ReplayFilesTest.java) passed 26 assertions on a macOS JVM. It checks malformed input, progress/completion separation, restart preservation, blocked output paths, failed replacement cleanup and a completion-only write failure. Its continuation loop checks that the storage helper returns an error rather than throwing; it does not execute `MainActivity`, Android's filesystem provider or JNI. Actual Android execution is recorded separately.

Each result file is replaced atomically on its own. The progress files and completion file are not a single transaction; failure in any requested write prevents the UI from claiming that all results were saved. These checks do not measure write latency, power-loss durability, camera acquisition or clinical accuracy.

Recorded results: [Linux assertions](../../validation/native-platforms/linux-io-tests.json), [JVM summary](../../validation/native-platforms/android-jvm-io-tests.json) and [JVM output](../../validation/native-platforms/android-jvm-io-tests.log).
