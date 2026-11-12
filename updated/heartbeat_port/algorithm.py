"""Faithful Python port of the original HeartBeat ``Algorithm.mm`` state machine.

Original: ``source/Heartbeat/Algorithm.{h,mm}`` (Or Maayan / Michael Leybovich,
2013), pinned upstream d5179096b96941bc0ff6aa8f0bacd88958dd37dd. Unmodified.

Per camera frame the original app:

1. averages every BGRA pixel of a 352x288 frame (``averageColorPrecise``),
2. takes the *green* component (``getColorValueFrom:`` -> ``green * 255``),
3. once more than ``filterWindowSize`` frames exist, takes the latest
   ``filterWindowSize + 1`` samples, subtracts their mean and re-filters them
   from zero state with an order-5 Butterworth band-pass (0.04-0.2 of Nyquist,
   i.e. 36-180 beats/min at 30 fps),
4. tests whether the sample ``windowSize + 1`` frames ago is greater than
   earlier neighbours and at least as great as later neighbours in a
   ``2*windowSize + 1`` window (with a ``windowSize``-frame refractory period),
5. counts peaks over a ``calibrationDuration``-frame window, converts the count
   to beats/min and smooths it with running weighted averages.

Everything below keeps the original indices, unsigned-arithmetic intent,
constants and quirks. Quirks that are *reproduced on purpose* (because they
change the output) are listed in ``ORIGINAL_QUIRKS``.

Deviations: the per-peak ``printf`` and ``NSLog`` calls are not reproduced;
there is no UIKit dependency (callers pass the green component directly);
``CGFloat`` is treated as a 64-bit double (as on 64-bit iOS). The 2013 target
device (iPhone 5, 32-bit ARM) used 32-bit float ``CGFloat``, so tiny rounding
differences against that historical device are possible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .butterworth import butter, filter_original

# Constants copied from Algorithm.mm
FPS = 30
WINDOW_SIZE = 9
WINDOW_SIZE_FOR_FILTER_CALCULATION = 60
CALIBRATION_DURATION = 90
WINDOW_SIZE_FOR_AVERAGE_CALCULATION = 75
FILTER_ORDER = 5
FILTER_LOWER_BAND = 0.04  # 36 bpm at 30 fps
FILTER_UPPER_BAND = 0.2   # 180 bpm at 30 fps
FINAL_RESULT_MARGIN = 1.5
DEFAULT_BPM_VALUE = 72
MIN_BPM_VALUE = 36
MAX_BPM_VALUE = 180

ORIGINAL_QUIRKS = (
    "isMissedPeak reads bpmAverageValues[framesCounter-windowSize-1] before that slot is "
    "updated in the current frame, so it always sees the DEFAULT_BPM_VALUE placeholder (72), "
    "not the latest estimate: after calibration a peak is forced whenever more than "
    "1.5 * 25 = 37.5 frames pass without one, whatever the measured rate.",
    "'int calibrationWeight = 2.5' truncates to 2.",
    "shouldShowLatestResult is sticky: once it returns YES it never returns NO again.",
    "lastPeakPlace is not updated in the pre-calibration first-peak branch (it returns early).",
    "Each frame re-filters a fresh window from zero initial state (no streaming filter state).",
    "isCalibrationOver does not require a detected peak: with firstPeakPlace == 0 it becomes "
    "true after calibrationDuration + filterWindowSize frames, so a flat (pulseless) signal "
    "reports the 72 bpm placeholder as a final result. The app relied on a separate "
    "red < 210 finger-presence check in VideoManagerViewController.",
)


@dataclass
class FrameTrace:
    """State observed after one ``new_frame`` call (mirrors the C++ harness CSV)."""

    frame: int
    value: float
    peak_index: int  # index (i-w-1) of the sample judged this frame, -1 if none
    is_peak: int
    bpm_value: float
    bpm_average: float
    calibration_over: int
    bpm_latest: float
    final_determined: int
    should_show: int
    missed_last_peak: int


class HeartbeatAlgorithm:
    """Port of the Objective-C ``Algorithm`` class.

    Properties that were lazy getters with defaults in the original are plain
    constructor arguments here. ``algorithm2`` in the original app used
    ``window_size=9, filter_window_size=45``.
    """

    def __init__(self, frame_rate: float = FPS, window_size: int = WINDOW_SIZE,
                 filter_window_size: int = WINDOW_SIZE_FOR_FILTER_CALCULATION,
                 calibration_duration: int = CALIBRATION_DURATION,
                 window_size_for_average: int = WINDOW_SIZE_FOR_AVERAGE_CALCULATION):
        self.frame_rate = float(frame_rate)
        self.window_size = int(window_size)
        self.filter_window_size = int(filter_window_size)
        self.calibration_duration = int(calibration_duration)
        self.window_size_for_average = int(window_size_for_average)
        self.b, self.a = butter((FILTER_LOWER_BAND, FILTER_UPPER_BAND), FILTER_ORDER)

        self.frames_counter = 0
        self.first_peak_place = 0  # 0 means "none found" in the original
        self.num_of_peaks = 0
        self.last_peak_place = 0
        self.points: List[float] = []
        self.bpm_values: List[float] = []
        self.bpm_average_values: List[float] = []
        self.is_peak: List[int] = []
        self.is_peak_in_last_frame = False
        self.is_missed_the_last_peak = False
        self._should_show_latest_result = False
        self._is_final_result_determined = False
        self.last_judged_index: Optional[int] = None

    # ------------------------------------------------------------------ getters
    @property
    def is_calibration_over(self) -> bool:
        fc = self.frames_counter
        return (fc > self.calibration_duration + self.filter_window_size
                and fc > self.calibration_duration + self.first_peak_place + self.window_size)

    @property
    def bpm_latest_result(self) -> float:
        if self.is_calibration_over:
            return self.bpm_average_values[self.frames_counter - self.window_size - 1]
        return 0.0

    def is_final_result_determined(self) -> bool:
        """Getter with side effects in the original (stores the last answer)."""
        if self.is_calibration_over:
            fc, w, calib = self.frames_counter, self.window_size, self.calibration_duration
            latest = self.bpm_latest_result
            half = calib // 2  # (int)(self.calibrationDuration/2) on NSUInteger
            if (abs(latest - self.bpm_average_values[fc - half - w - 1]) <= FINAL_RESULT_MARGIN * 2 / 3
                    and abs(latest - self.bpm_average_values[fc - calib - w - 1]) <= FINAL_RESULT_MARGIN):
                self._is_final_result_determined = True
                return True
            self._is_final_result_determined = False
        else:
            self._is_final_result_determined = False
        return self._is_final_result_determined

    def should_show_latest_result(self) -> bool:
        """Sticky getter, exactly as in the original."""
        fc, w, calib = self.frames_counter, self.window_size, self.calibration_duration
        avg = self.bpm_average_values
        if self.is_calibration_over and fc > calib + self.first_peak_place + w + self.window_size_for_average:
            if abs(avg[fc - calib - w - 1] - avg[fc - calib - w - 2]) < 0.083:
                if abs(avg[fc - calib // 2 - w - 1] - avg[fc - calib // 2 - w - 2]) < 0.066:
                    if abs(avg[fc - w - 1] - avg[fc - w - 2]) < 0.05:
                        self._should_show_latest_result = True
        return self._should_show_latest_result

    # ------------------------------------------------------------------ helpers
    def _is_peak(self, graph: List[float], window: int) -> bool:
        since_last = self.frames_counter - window - 1 - self.last_peak_place
        if 0 <= since_last < window:  # unsigned wrap in the original makes negatives "large"
            return False
        middle = graph[window]
        for i in range(window):
            if middle <= graph[i]:
                return False
        for i in range(window + 1, 2 * window + 1):
            if middle < graph[i]:
                return False
        return True

    def _is_missed_peak(self) -> bool:
        latest = self.bpm_latest_result
        if latest == 0:
            # 1/(0/(60*fps)) is +inf in IEEE arithmetic; comparison is then false.
            return False
        expected = 1 / (latest / (60 * self.frame_rate))
        margin_factor = 0.5
        return (self.frames_counter - self.window_size - 1 - self.last_peak_place
                > (1 + margin_factor) * expected)

    # ------------------------------------------------------------------ main API
    def new_frame_with_green_component(self, green_component: float) -> None:
        """Equivalent of ``newFrameDetectedWithAverageColor:``.

        ``green_component`` is the UIColor green channel in [0, 1]; the
        original multiplies it by 255 in ``getColorValueFrom:``.
        """
        self.is_final_result_determined()  # evaluated (and ignored) at the top of the original

        self.frames_counter += 1
        self.points.append(green_component * 255.0)
        self.is_peak.append(0)
        self.bpm_values.append(float(DEFAULT_BPM_VALUE))
        self.bpm_average_values.append(float(DEFAULT_BPM_VALUE))
        self.last_judged_index = None

        i = self.frames_counter
        w = self.window_size
        calib = self.calibration_duration

        if i <= self.filter_window_size:
            return

        n = self.filter_window_size + 1
        x = self.points[-n:]
        mean = 0.0
        for v in x:
            mean += v
        mean = mean / n
        x = [v - mean for v in x]
        y = filter_original(2 * FILTER_ORDER, self.a, self.b, x)
        z = y[n - 2 * w - 1:]
        idx = i - w - 1
        self.last_judged_index = idx

        if not self.first_peak_place:
            self.is_peak[idx] = int(self._is_peak(z, w))
            self.num_of_peaks += self.is_peak[idx]
            if self.is_peak[idx]:
                self.first_peak_place = idx
                self.bpm_values[idx] = 0.0
                self.bpm_average_values[idx] = 0.0
            return

        if i < calib + self.first_peak_place + w + 1:
            self.is_peak[idx] = int(self._is_peak(z, w))
            self.num_of_peaks += self.is_peak[idx]
            frames = i - self.first_peak_place - 1
            if frames > calib:
                frames = calib
            bpm = (self.num_of_peaks / (frames / self.frame_rate)) * 60
            self.bpm_values[idx] = float(min(max(bpm, MIN_BPM_VALUE), MAX_BPM_VALUE))
            k = i - (self.first_peak_place + w + 1) - 1 + 4.5
            sensitive = 1.5
            self.bpm_average_values[idx] = (self.bpm_average_values[idx - 1] * k / (k + sensitive)
                                            + self.bpm_values[idx] * sensitive / (k + sensitive))
        else:
            if i < calib + (self.first_peak_place + w + 1) + 2.5 * 30:
                self.is_peak[idx] = int(self._is_peak(z, w))
            else:
                self.is_peak[idx] = 1 if self._is_missed_peak() else int(self._is_peak(z, w))
                self.is_missed_the_last_peak = self._is_missed_peak()
            self.num_of_peaks += self.is_peak[idx] - self.is_peak[idx - calib]
            frames = calib
            bpm = (self.num_of_peaks / (frames / self.frame_rate)) * 60
            self.bpm_values[idx] = float(min(max(bpm, MIN_BPM_VALUE), MAX_BPM_VALUE))
            m = self.window_size_for_average
            temp = 0.0
            for j in range(1, m + 1):
                temp += self.bpm_values[idx - m + j]
            average_bpm = temp / m
            calibration_weight = int(2.5)  # original: int calibrationWeight = 2.5;
            sensitive = 2.5
            k = i - (calib + self.first_peak_place + w + 1) + calibration_weight
            self.bpm_average_values[idx] = (self.bpm_average_values[idx - 1] * k / (k + sensitive)
                                            + average_bpm * sensitive / (k + sensitive))

        self.is_peak_in_last_frame = bool(self.is_peak[idx])
        if self.is_peak[idx]:
            self.last_peak_place = idx

    def new_frame_with_mean_green(self, mean_green_0_255: float) -> None:
        """Convenience wrapper taking an average green value in [0, 255]."""
        self.new_frame_with_green_component(mean_green_0_255 / 255.0)

    def trace_frame(self, green_component: float) -> FrameTrace:
        """Process one frame and return the same fields the C++ harness prints.

        The harness queries the public getters in this order after each frame,
        matching how ``VideoManagerViewController`` polled them each frame.
        """
        self.new_frame_with_green_component(green_component)
        idx = self.last_judged_index
        calibration_over = self.is_calibration_over
        latest = self.bpm_latest_result
        final = self.is_final_result_determined()
        show = self.should_show_latest_result()
        last = self.frames_counter - 1
        return FrameTrace(
            frame=self.frames_counter,
            value=self.points[-1],
            peak_index=-1 if idx is None else idx,
            is_peak=0 if idx is None else self.is_peak[idx],
            bpm_value=self.bpm_values[idx if idx is not None else last],
            bpm_average=self.bpm_average_values[idx if idx is not None else last],
            calibration_over=int(calibration_over),
            bpm_latest=latest,
            final_determined=int(final),
            should_show=int(show),
            missed_last_peak=int(self.is_missed_the_last_peak),
        )


def run_on_green_components(components, **kwargs) -> List[FrameTrace]:
    alg = HeartbeatAlgorithm(**kwargs)
    return [alg.trace_frame(c) for c in components]
