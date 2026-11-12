"""SYNTHETIC test signals. Not recordings, and not evidence of real-world accuracy.

These generators make a fingertip-like reflectance trace for deterministic
tests and demonstrations. The waveform model (a skewed pulse, slow drift and
seeded Gaussian noise) is an assumption of this modernization. It is not taken
from the original project or its report. Results on these signals say nothing
about the accuracy reported for the 2013 iPhone app.
"""

from __future__ import annotations

import math
import random
from typing import List


def synthetic_ppg_green_components(bpm: float, seconds: float, fps: float = 30.0,
                                   baseline: float = 0.35, amplitude: float = 0.01,
                                   drift: float = 0.004, noise: float = 0.0015,
                                   seed: int = 0) -> List[float]:
    """SYNTHETIC green-channel components in [0, 1], one per frame.

    Blood volume increases absorb more light, so the pulse is a dip in
    reflected intensity: each beat has a fast downstroke and slower recovery.
    """
    rng = random.Random(seed)
    n = int(round(seconds * fps))
    f_beat = bpm / 60.0
    out = []
    for k in range(n):
        t = k / fps
        phase = (t * f_beat) % 1.0
        # skewed pulse: fast rise to peak absorption at phase 0.15, slow decay
        if phase < 0.15:
            pulse = phase / 0.15
        else:
            pulse = math.exp(-(phase - 0.15) / 0.25)
        value = (baseline - amplitude * pulse
                 + drift * math.sin(2 * math.pi * 0.1 * t)
                 + rng.gauss(0.0, noise))
        out.append(min(1.0, max(0.0, value)))
    return out


def synthetic_bgra_frame(green_component: float, width: int = 352, height: int = 288,
                         seed: int = 0) -> bytes:
    """SYNTHETIC BGRA frame whose mean green is approximately ``green_component``.

    Red is saturated, as in a torch-lit fingertip, and blue is dark.
    """
    rng = random.Random(seed)
    g = green_component * 255.0
    buf = bytearray(width * height * 4)
    for p in range(width * height):
        gv = int(min(255, max(0, round(g + rng.uniform(-2, 2)))))
        buf[4 * p + 0] = 10
        buf[4 * p + 1] = gv
        buf[4 * p + 2] = 250
        buf[4 * p + 3] = 255
    return bytes(buf)
