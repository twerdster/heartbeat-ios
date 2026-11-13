# Repaired native filter

`Butterworth.cpp` is a separately labeled copy of the original, with its notices retained. Original source pin: `d5179096b96941bc0ff6aa8f0bacd88958dd37dd`.

Original SHA-256: `0f30661515bea6c1c6c0d364363358743729446b3835fc051111249775a2224d`.
Repaired SHA-256: `6336eddde55001c4534c481a70305dd1515e46b7b23d99d06a4c252dba56e86e`.

Only `filter()` changes: return for empty/invalid arguments, bound startup by sample count, and stop the main loop at `i < np`. No coefficient design, peak detection or BPM calculation is replaced. Other routines are unchanged; `ComputeNumCoeffs` still supports only design orders up to 5. The supported heartbeat design order remains 5.

The CMake target compiles this filter; the macOS harness substitutes it into the unchanged original `Algorithm.mm`. `filter_regression.cpp` checks seven lengths each against independent order-2 and order-10 direct recurrences. The order-10 coefficients are the saved original order-5 bandpass fixture. ASan/UBSan checks are scoped to that invocation. The full Objective-C++ replay uses ASan (not leak checking); its 90-frame fixture completes after the original aborts while processing frame 61 (60 rows completed).

The Python `heartbeat_port/corrected.py` is separate new behavior: observed-peak calibration, no fabricated missed beats, constant-input withholding and timestamp/gap handling. It is not part of this native filter repair.
