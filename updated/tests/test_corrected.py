"""Constructed-input regressions for separately labeled corrected behavior."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from heartbeat_port import HeartbeatAlgorithm
from heartbeat_port.corrected import CorrectedHeartbeatAlgorithm, TimestampedHeartbeat
from heartbeat_port.synthetic import synthetic_ppg_green_components


class CorrectedTests(unittest.TestCase):
    def test_flat_input_does_not_report_placeholder(self):
        legacy=HeartbeatAlgorithm()
        fixed=TimestampedHeartbeat()
        for n in range(600):
            legacy.new_frame_with_green_component(.5)
            result=fixed.update(n/30,.5)
        self.assertEqual(legacy.bpm_latest_result,72)
        self.assertTrue(legacy.is_final_result_determined())
        self.assertIsNone(result.bpm)
        self.assertEqual(result.status,'flat_input')
        self.assertFalse(fixed.algorithm.is_calibration_over)

    def test_periodic_signal_estimates_known_rate(self):
        fixed=TimestampedHeartbeat()
        estimates=[]
        for n,value in enumerate(synthetic_ppg_green_components(84,30,seed=3)):
            result=fixed.update(n/30,value)
            if n>=600 and result.bpm is not None: estimates.append(result.bpm)
        self.assertGreater(len(estimates),250)
        self.assertLess(sum(abs(x-84) for x in estimates)/len(estimates),5)

    def test_no_forced_peaks(self):
        fixed=CorrectedHeartbeatAlgorithm()
        for value in synthetic_ppg_green_components(84,15,seed=3):
            fixed.new_frame_with_green_component(value)
        for _ in range(90):fixed.new_frame_with_green_component(.5)
        # The restarted short-window filter can ring at the transition. After
        # three seconds of constant input, no continuing periodic peaks occur.
        before=sum(fixed.is_peak)
        for _ in range(210):fixed.new_frame_with_green_component(.5)
        self.assertEqual(sum(fixed.is_peak),before)
        self.assertFalse(fixed._is_missed_peak())

    def test_irregular_sampling_resamples_and_gap_resets(self):
        fixed=TimestampedHeartbeat()
        for n in range(151):result=fixed.update(n/25,.5+.1*math.sin(n/25*2*math.pi*1.4))
        self.assertEqual(result.resampled_frames,181)
        result=fixed.update(7.,.5)
        self.assertEqual(result.status,'gap_reset')
        self.assertEqual(result.resampled_frames,1)
        self.assertIsNone(result.bpm)

    def test_invalid_samples_and_nonincreasing_times(self):
        fixed=TimestampedHeartbeat()
        for value in [float('nan'),float('inf'),-0.1,1.1]:
            with self.assertRaises(ValueError):fixed.update(0.,value)
        fixed.update(0.,.5)
        for time in [0.,-.1]:
            with self.assertRaises(ValueError):fixed.update(time,.5)


if __name__=='__main__':unittest.main()
