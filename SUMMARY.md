# heartbeat-ios: maintenance context

Read this file first, then SKILL.md and README.md. This context describes the repository as of 2026-11-13.

## Purpose and current source

Historical iPhone green-channel pulse-estimation prototype by Or Maayan and Michael Leybovich (report About us section and source copyright headers), with an updated Python filter/peak/BPM component.

Original source is unchanged submodule source/ at d5179096b96941bc0ff6aa8f0bacd88958dd37dd. The Python component handles supplied samples/BGRA buffers, not camera capture or the iOS UI.

## Use and validation

From updated/ (submodule required only for the live original-code comparison): python3 demo.py --bpm 84 --seconds 30; python3 -m unittest discover -s tests -v. updated/README.md has setup/commands; updated/ALGORITHM.md has the chain, deviations and comparison detail.

updated/VALIDATION.json records 20 component tests and six real notebook code cells passed on 2026-11-12, macOS 15.1.1 arm64 / Python 3.14.4. The saved maintenance log confirms the live compiled-original comparison passed among all 20 tests (no skip). A minimal UIKit shim runs unchanged original Objective-C++ algorithm code for exact synthetic green-component trace comparison. It does not build the app or establish raw-frame parity/measurement accuracy.

The port avoids the original filter overflow, but keeps the 72 bpm flat-input placeholder and related missed-peak quirks. Raw-frame scaling precision differs; the historical 32-bit device differs from the 64-bit Mac harness. iOS app/device/Linux execution is unvalidated; physical camera/flash, Core Plot and Facebook SDK integration are unresolved. Research software, not a medical device.

## Documentation maintenance

The 2026-11-12 documentation revision organizes the README around implementation, available source, setup, recorded checks and limits. It preserves historical visuals and links, with captions separating historical results from updated examples. No runnable code, source provenance, pinned revisions, licenses or validation results changed in this revision. Recorded earlier tests were not rerun for the prose-only edits.

Preserve original source and authorship. New ports belong under updated/ and require their own scope/validation. Do not infer a blanket license from recovery. Review this file and SKILL.md before every commit and synchronize changes to workflow, commands, validation or status. Check relative links and figure rendering; never describe inventory counts or component tests as full-application validation.

Two actual Claude editorial review rounds on 2026-11-12 covered the README and related changed documentation, including context files, component guides and applicable algorithm/build notes or schematic text. Useful qualifications were checked against source, preserved project records and saved validation logs, then applied. Editorial review adds no runtime coverage.

## Author correspondence recorded on 2026-11-13

On 2026-11-12, Michael Leybovich confirmed that he was comfortable with Aaron Wetzler keeping the archival project page and repository. This records Michael Leybovich's response only; it does not replace the existing source notices or third-party terms. No new software license is added.

This update changes documentation only. Source files, pinned revisions, assets, licenses and recorded validation results are unchanged. Private correspondence remains outside the repository. No new build, runtime or numerical validation was performed for this update.

Two actual Claude editorial rounds on 2026-11-13 reviewed these author-correspondence notes and the related documentation/context changes. Minor factual and wording corrections were applied against the correspondence and existing repository records. This review and documentation update add no runtime validation.
