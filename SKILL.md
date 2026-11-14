# Maintaining heartbeat-ios

Read SUMMARY.md first, then this file, the root project reference, updated/README.md, updated/RUNNING_2026.md, validation records and relevant source.

## Preservation and workflow

Keep the root README unchanged unless Aaron explicitly requests edits there. Preserve original source bytes/pins, author/student/third-party attribution, notices and permission scope. Put new code, adapters, behavioral changes, guides and result media under updated/. Never imply that a declaration-only header or headless core is a restored historical app. See the running guide for current commands/dependencies rather than duplicating them here.

## Evidence

Use updated/VALIDATION.json and updated/validation/2026-11-14/ for current results and limits. Keep earlier notebook results dated; do not imply they were rerun. Distinguish original code, native repairs, Python translation, optional behavior/output filters, actual input data, synthetic fixtures and saved playback. State the tested implementation, platform, operator chain, counts, units and reference provenance. One sequence does not establish general correctness, accuracy or clinical/device compatibility.

Compare fixes with reproduced failures and affected tests/sanitizers. Retain raw output when new processing changes presentation. Follow SUMMARY.md for SSD data paths; recheck mount identity/space/write access before bulk writes. Keep native builds/environments off exFAT. Preserve private correspondence/contact details outside the public repository; an author's response does not assign a blanket license.

## Before every commit

Reread and synchronize SUMMARY.md and this file whenever behavior, commands, outputs, workflow or status changes. Verify original source hashes/pins and root README identity. Check changed Markdown, links/images, media limits and diff scope; run meaningful affected checks after code changes. No package bundles these documentation files. Keep Claude review claims tied to completed reviews and factual checks; editorial review adds no runtime coverage.

## Native interface maintenance

See `updated/platforms/NATIVE.md` for CMake, Xcode, Gradle and Tk commands; use `updated/validation/native-platforms/` for actual execution records. Keep state-machine parity separate from signal accuracy, new replay interfaces separate from the recovered camera app, and app recordings separate from supplied data and generated plots. Android uses JNI and Linux uses ctypes to call the same C++ core. A PPG replay does not establish camera support.

Reuse SDKs from private task storage, without committing signing or device identifiers. Bundle the BIDMC data notice. Publish actual app captures with precise platform and input labels; identify Linux Xvfb as a virtual display. Keep the native implementation, recorded source hashes, build commands, result schema and capture provenance synchronized. Check output-write errors before describing results as saved.

Use the tests in `updated/platforms/tests/` and the Android helper regression for checked-save behavior. Preserve completed-only records during partial restarts; atomically replace individual output files and report write errors. Do not infer a current run from an old completion file: bind captures, source and binary hashes to the run. Retest output recovery after save-path changes; UI automation or static review alone does not establish numerical parity.
