"""Separately labeled behavioral fixes, retaining the original filter/peak chain.

This mode gates flat input, requires observed peaks before calibration, avoids
inventing missed peaks, and interpolates supplied timestamps onto the original 30 Hz
grid. It is not a camera adapter or a clinical signal-quality classifier.
"""
from collections import deque
from dataclasses import dataclass
import math

from .algorithm import HeartbeatAlgorithm


class CorrectedHeartbeatAlgorithm(HeartbeatAlgorithm):
    @property
    def is_calibration_over(self):
        return bool(self.first_peak_place) and super().is_calibration_over

    def _is_missed_peak(self):
        # A missing observation is not evidence of a new beat.
        return False

    def new_frame_with_green_component(self, value):
        if not math.isfinite(value) or not 0<=value<=1:
            raise ValueError('green component must be finite and in [0,1]')
        super().new_frame_with_green_component(value)


@dataclass
class Estimate:
    timestamp: float
    bpm: float | None
    status: str
    observed_peaks: int
    resampled_frames: int


class TimestampedHeartbeat:
    """Linear timestamp resampling and explicit gaps around the corrected core.

    Interpolation uses consecutive sample brackets (up to one input interval of
    latency in streaming use). A gap greater than max_gap_seconds resets state. Constant two-second input
    is withheld. Neither gate distinguishes every noisy signal from a pulse.
    """
    def __init__(self, max_gap_seconds=0.2):
        if not math.isfinite(max_gap_seconds) or max_gap_seconds<=1/30:
            raise ValueError('maximum gap must exceed one 30 Hz interval')
        self.max_gap_seconds=max_gap_seconds
        self.algorithm=CorrectedHeartbeatAlgorithm()
        self.previous=None
        self.origin=None
        self.ticks=0
        self.recent=deque(maxlen=60)
        self.observed_peaks=0

    def _push(self, green):
        self.algorithm.new_frame_with_green_component(green)
        self.recent.append(green)
        index=self.algorithm.last_judged_index
        if index is not None and self.algorithm.is_peak[index]:
            self.observed_peaks+=1

    def update(self, timestamp, green):
        if not math.isfinite(timestamp) or not math.isfinite(green) or not 0<=green<=1:
            raise ValueError('finite timestamp and green component in [0,1] required')
        gap=False
        if self.previous is not None:
            if timestamp<=self.previous[0]:
                raise ValueError('timestamps must increase strictly')
            gap=timestamp-self.previous[0]>self.max_gap_seconds
        if self.origin is None or gap:
            self.algorithm=CorrectedHeartbeatAlgorithm()
            self.recent.clear()
            self.previous=(timestamp,green)
            self.origin=timestamp
            self.ticks=1
            self.observed_peaks=0
            self._push(green)
        else:
            lo, value=self.previous
            target=self.origin+self.ticks/30
            while target<=timestamp+1e-9:
                alpha=min(1.,max(0.,(target-lo)/(timestamp-lo)))
                sample=value+alpha*(green-value)
                self._push(sample)
                self.ticks+=1
                target=self.origin+self.ticks/30
            self.previous=(timestamp,green)
        alg=self.algorithm
        observed=self.observed_peaks
        status='warming_up'
        bpm=None
        if gap:
            status='gap_reset'
        elif len(self.recent)==60 and max(self.recent)-min(self.recent)<1e-9:
            status='flat_input'
        elif alg.is_calibration_over and observed>=3:
            since_peak=alg.frames_counter-alg.last_peak_place
            if since_peak<=60:
                bpm=alg.bpm_latest_result
                if math.isfinite(bpm) and 36<=bpm<=180:
                    status='estimated'
                else:
                    bpm=None
        return Estimate(timestamp,bpm,status,observed,alg.frames_counter)
