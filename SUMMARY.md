# HeartBeat: current maintenance context

Read this file, then SKILL.md, README.md and linked implementation/validation guides.

## Original project and preservation

Pulse-estimation project by Or Maayan and Michael Leybovich, supervised by Aaron Wetzler. The unchanged source submodule is pinned at d5179096b96941bc0ff6aa8f0bacd88958dd37dd. Python/C++ processing and native replay interfaces are separate updated work.

## Current work — 2026-11-17

The new static page replays the saved BIDMC01 PPG and 1 Hz legacy/guarded/ECG traces. It does not execute the estimator or collect camera samples. Existing numerical/native checks remain recorded at their original dates; they were not rerun for the replay page. The original camera app remains blocked by FacebookSDK headers.

Aaron requested concise natural README prose and a runnable demo in each Updated section. A real tools-disabled Claude review and follow-up inform the wording; factual suggestions are checked against source and records. The previous full README is preserved as PROJECT_RECORD.md. Existing updated-guide anchors remain available; lengthy implementation/recovery records are linked rather than repeated in the main README.

## Checks and maintenance

Preserve source submodule/pin and notices. updated/DETAILS.md retains full processing/native results and qualifications. Use updated/VALIDATION.json and dated validation directories for exact numerical claims. Native interfaces process supplied PPG, not restored camera capture; single-record parity/error does not establish clinical accuracy. Keep BIDMC attribution and distinguish source rights from data licensing.

New static demonstration checks are in updated/demo/VALIDATION.json when present. Actual Chrome desktop/390-pixel interactions were checked; a narrow viewport is not a physical device. No hardware, live microphone/camera recognition or cross-browser coverage is added. Review and synchronize SUMMARY.md and SKILL.md before every commit. Keep private evidence, account details and machine paths outside the repository.

The historical original-app build excerpt now uses checkout-relative `source/` paths. Four private checkout prefixes were sanitized on 2026-11-17, preserving exact compiler diagnostics and failure status; the raw excerpt is retained privately. Before publishing logs, check for personal host/workspace prefixes and document any sanitization without implying a new build.
