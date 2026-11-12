"""Tests for the HeartBeat port. Run from updated/: python3 -m unittest discover -s tests -v

All signals are SYNTHETIC (heartbeat_port.synthetic). Passing tests show fidelity
to the original code and sane behaviour on synthetic data only, not the accuracy
of the 2013 app on people.
"""

from __future__ import annotations

import csv
import dataclasses
import math
import shutil
import sys
import unittest
from pathlib import Path

UPDATED = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UPDATED))
sys.path.insert(0, str(UPDATED / "harness"))

from heartbeat_port import (HeartbeatAlgorithm, average_color_precise_bgra, butter,  # noqa: E402
                            filter_original, frequency_response, run_on_green_components)
from heartbeat_port.synthetic import synthetic_bgra_frame, synthetic_ppg_green_components  # noqa: E402

FIX = UPDATED / "tests" / "fixtures"
FIELDS = [f.name for f in dataclasses.fields(__import__("heartbeat_port").FrameTrace)]


def load_components(path: Path):
    return [float(ln) for ln in path.read_text().splitlines() if ln and not ln.startswith("#")]


def load_trace(path: Path):
    return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(path.read_text().splitlines())]


class ButterworthTests(unittest.TestCase):
    def setUp(self):
        self.b, self.a = butter((0.04, 0.2), 5)

    def test_matches_original_coefficients_bit_for_bit(self):
        rows = list(csv.DictReader((FIX / "original_butter_coeffs.csv").read_text().splitlines()))
        self.assertEqual(len(rows), 11)
        for r in rows:
            k = int(r["k"])
            self.assertEqual(self.b[k], float(r["b"]), f"b[{k}]")
            self.assertEqual(self.a[k], float(r["a"]), f"a[{k}]")

    def test_band_edges_are_minus_3db(self):
        for f in (0.04, 0.2):
            g = abs(frequency_response(self.b, self.a, math.pi * f))
            self.assertAlmostEqual(g, 1 / math.sqrt(2), delta=1e-7)

    def test_unit_gain_at_normalisation_frequency_and_zeros_at_dc_nyquist(self):
        cp0 = 4.0 * math.tan(math.pi * 0.04 / 2)
        cp1 = 4.0 * math.tan(math.pi * 0.2 / 2)
        wn = 2 * math.atan2(math.sqrt(cp0 * cp1), 4)
        self.assertAlmostEqual(abs(frequency_response(self.b, self.a, wn)), 1.0, places=9)
        self.assertLess(abs(frequency_response(self.b, self.a, 0.0)), 1e-12)
        self.assertLess(abs(frequency_response(self.b, self.a, math.pi)), 1e-12)

    def test_numerator_is_scaled_band_pass_binomial(self):
        pattern = [1, 0, -5, 0, 10, 0, -10, 0, 5, 0, -1]
        g = self.b[0]
        for bk, pk in zip(self.b, pattern):
            self.assertAlmostEqual(bk, g * pk, delta=1e-15)

    def test_filter_is_stable(self):
        x = [1.0] + [0.0] * 3999
        y = filter_original(10, self.a, self.b, x)
        self.assertLess(max(abs(v) for v in y[-500:]), 1e-9)

    def test_filter_matches_direct_difference_equation(self):
        import random
        rng = random.Random(5)
        x = [rng.uniform(-1, 1) for _ in range(61)]
        y = filter_original(10, self.a, self.b, x)
        for n in range(len(x)):
            acc = sum(self.b[j] * x[n - j] for j in range(11) if n - j >= 0)
            acc -= sum(self.a[j] * y[n - j] for j in range(1, 11) if n - j >= 0)
            self.assertAlmostEqual(y[n], acc, places=12)

    def test_order_above_original_table_is_rejected(self):
        with self.assertRaises(ValueError):
            butter((0.04, 0.2), 6)


class FrameAveragingTests(unittest.TestCase):
    def test_average_color_precise_channel_order(self):
        w, h = 3, 2
        buf = bytearray()
        for p in range(w * h):
            buf += bytes([p, 100 + p, 200 + p, 255])  # B, G, R, A
        r, g, b = average_color_precise_bgra(bytes(buf), w, h)
        self.assertAlmostEqual(g * 255, 102.5, places=12)
        self.assertAlmostEqual(r * 255, 202.5, places=12)
        self.assertAlmostEqual(b * 255, 2.5, places=12)

    def test_row_padding_is_respected(self):
        w, h, bpr = 2, 2, 12  # 4 bytes of padding per row
        buf = bytearray(bpr * h)
        for row in range(h):
            for col in range(w):
                buf[row * bpr + col * 4 + 1] = 50
            buf[row * bpr + 9] = 255  # padding must be ignored
        self.assertAlmostEqual(average_color_precise_bgra(bytes(buf), w, h, bpr)[1] * 255, 50.0)

    def test_invalid_geometry_is_rejected(self):
        for width, height, stride in ((0, 2, 0), (2, 0, 8), (-1, 2, 8), (2, 2, 4)):
            with self.subTest(width=width, height=height, stride=stride):
                with self.assertRaises(ValueError):
                    average_color_precise_bgra(bytes(32), width, height, stride)
        with self.assertRaises(ValueError):
            average_color_precise_bgra(bytes(3), 1, 1)


class AlgorithmFidelityTests(unittest.TestCase):
    def _compare(self, name, **kw):
        comps = load_components(FIX / f"{name}_input.txt")
        orig = load_trace(FIX / f"{name}_original_trace.csv")
        port = run_on_green_components(comps, **kw)
        self.assertEqual(len(orig), len(port))
        for o, p in zip(orig, port):
            for k in FIELDS:
                self.assertEqual(o[k], float(getattr(p, k)), f"frame {int(o['frame'])} field {k}")

    def test_matches_original_trace_default_configuration(self):
        self._compare("synthetic_72bpm_seed1")

    def test_matches_original_trace_algorithm2_configuration(self):
        self._compare("synthetic_110bpm_seed7_alg2", window_size=9, filter_window_size=45)

    @unittest.skipUnless(shutil.which("clang++") and sys.platform == "darwin", "needs Apple clang + Foundation")
    def test_live_against_freshly_compiled_original(self):
        from compare_with_original import compare
        for bpm, seed in [(48, 11), (150, 12)]:
            r = compare(synthetic_ppg_green_components(bpm, 35, seed=seed), "strict")
            self.assertEqual(r["exact_rows"], r["frames"], f"{bpm} bpm")
        r = compare([0.4] * 300, "strict")  # flat-signal quirk
        self.assertEqual(r["exact_rows"], r["frames"])


class AlgorithmBehaviourTests(unittest.TestCase):
    """Properties of the ported algorithm on SYNTHETIC signals."""

    def test_converges_near_synthetic_rate(self):
        for bpm in (54, 66, 84, 100, 126):
            tr = run_on_green_components(synthetic_ppg_green_components(bpm, 45, seed=bpm))
            self.assertTrue(tr[-1].calibration_over)
            self.assertLess(abs(tr[-1].bpm_latest - bpm), 3.0, f"{bpm}: {tr[-1].bpm_latest}")

    def test_no_result_before_calibration(self):
        alg = HeartbeatAlgorithm()
        for c in synthetic_ppg_green_components(80, 4, seed=1):  # 120 frames < 90 + 60
            alg.new_frame_with_green_component(c)
            self.assertFalse(alg.is_calibration_over)
            self.assertEqual(alg.bpm_latest_result, 0.0)

    def test_peaks_respect_refractory_window(self):
        alg = HeartbeatAlgorithm()
        for c in synthetic_ppg_green_components(170, 40, seed=2):
            alg.new_frame_with_green_component(c)
        peaks = [i for i, p in enumerate(alg.is_peak) if p]
        self.assertTrue(peaks)
        gaps = [b - a for a, b in zip(peaks, peaks[1:])]
        self.assertGreaterEqual(min(gaps), alg.window_size)

    def test_instantaneous_values_are_clamped(self):
        tr = run_on_green_components(synthetic_ppg_green_components(70, 40, seed=3))
        for t in tr:
            if t.peak_index >= 0 and t.bpm_value not in (0.0, 72.0):
                self.assertGreaterEqual(t.bpm_value, 36.0)
                self.assertLessEqual(t.bpm_value, 180.0)

    def test_flat_signal_reproduces_original_placeholder_quirk(self):
        # Verified against the compiled original: no peak is ever found, yet
        # calibration "completes" and the 72 bpm placeholder is reported as final.
        alg = HeartbeatAlgorithm()
        for _ in range(400):
            alg.new_frame_with_green_component(0.4)
        self.assertEqual(alg.first_peak_place, 0)
        self.assertEqual(sum(alg.is_peak), 0)
        self.assertTrue(alg.is_calibration_over)
        self.assertEqual(alg.bpm_latest_result, 72.0)
        self.assertTrue(alg.is_final_result_determined())

    def test_dc_offset_invariance(self):
        base = synthetic_ppg_green_components(90, 30, seed=4)
        a = run_on_green_components(base)
        b = run_on_green_components([c + 0.05 for c in base])
        self.assertEqual([t.is_peak for t in a], [t.is_peak for t in b])

    def test_end_to_end_from_synthetic_bgra_frames(self):
        comps = synthetic_ppg_green_components(75, 40, seed=9)
        alg = HeartbeatAlgorithm()
        for k, c in enumerate(comps):
            frame = synthetic_bgra_frame(c, 32, 24, seed=k)
            alg.new_frame_with_green_component(average_color_precise_bgra(frame, 32, 24)[1])
        self.assertLess(abs(alg.bpm_latest_result - 75), 4.0)


if __name__ == "__main__":
    unittest.main()
