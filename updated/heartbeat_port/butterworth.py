"""Line-by-line Python port of the original HeartBeat ``Butterworth.cpp``.

Original: ``source/Heartbeat/Butterworth.cpp`` (Or Maayan, 2013), pinned upstream
commit d5179096b96941bc0ff6aa8f0bacd88958dd37dd. The original file is not modified.

The arithmetic follows the original statement order so that, with
floating-point contraction disabled in the C++ build, results match
bit-for-bit on the same platform libm (see ``harness/``).

Documented deviations from the original C++:

* ``filter`` in the original writes ``y[np]`` and reads ``x[np]`` (its second
  loop runs ``i < np + 1``), one element past both arrays allocated by
  ``Algorithm.mm``. This port computes only ``y[0..np-1]``. The out-of-range
  element was never read by the app, so the in-range outputs are unchanged.
* ``ComputeNumCoeffs`` indexes a fixed ``Numbers[11]`` table, so orders above 5
  read past that table in the original. This port raises ``ValueError`` instead.
* The original leaks the ``calloc`` buffers; Python manages memory itself.
"""

from __future__ import annotations

import cmath
import math
from typing import List, Sequence, Tuple

MAX_ORIGINAL_ORDER = 5  # Numbers[11] in ComputeNumCoeffs supports 2*order+1 <= 11


def compute_lp(order: int) -> List[float]:
    """Port of ``ComputeLP``: binomial numerator coefficients."""
    num = [0.0] * (order + 1)
    num[0] = 1.0
    num[1] = float(order)
    m = order // 2
    for i in range(2, m + 1):
        num[i] = float(order - i + 1) * num[i - 1] / i
        num[order - i] = num[i]
    num[order - 1] = float(order)
    num[order] = 1.0
    return num


def compute_hp(order: int) -> List[float]:
    """Port of ``ComputeHP``: alternate-sign binomial coefficients."""
    num = compute_lp(order)
    for i in range(order + 1):
        if i % 2:
            num[i] = -num[i]
    return num


def trinomial_multiply(order: int, b: Sequence[float], c: Sequence[float]) -> List[float]:
    """Port of ``TrinomialMultiply`` (interleaved real/imag complex coefficients)."""
    ret = [0.0] * (4 * order)
    ret[2] = c[0]
    ret[3] = c[1]
    ret[0] = b[0]
    ret[1] = b[1]
    for i in range(1, order):
        ret[2 * (2 * i + 1)] += c[2 * i] * ret[2 * (2 * i - 1)] - c[2 * i + 1] * ret[2 * (2 * i - 1) + 1]
        ret[2 * (2 * i + 1) + 1] += c[2 * i] * ret[2 * (2 * i - 1) + 1] + c[2 * i + 1] * ret[2 * (2 * i - 1)]
        for j in range(2 * i, 1, -1):
            ret[2 * j] += (b[2 * i] * ret[2 * (j - 1)] - b[2 * i + 1] * ret[2 * (j - 1) + 1]
                           + c[2 * i] * ret[2 * (j - 2)] - c[2 * i + 1] * ret[2 * (j - 2) + 1])
            ret[2 * j + 1] += (b[2 * i] * ret[2 * (j - 1) + 1] + b[2 * i + 1] * ret[2 * (j - 1)]
                               + c[2 * i] * ret[2 * (j - 2) + 1] + c[2 * i + 1] * ret[2 * (j - 2)])
        ret[2] += b[2 * i] * ret[0] - b[2 * i + 1] * ret[1] + c[2 * i]
        ret[3] += b[2 * i] * ret[1] + b[2 * i + 1] * ret[0] + c[2 * i + 1]
        ret[0] += b[2 * i]
        ret[1] += b[2 * i + 1]
    return ret


def compute_den_coeffs(order: int, lcutoff: float, ucutoff: float) -> List[float]:
    """Port of ``ComputeDenCoeffs``; returns the 2*order+1 denominator taps (a)."""
    cp = math.cos(math.pi * (ucutoff + lcutoff) / 2.0)
    theta = math.pi * (ucutoff - lcutoff) / 2.0
    st = math.sin(theta)
    ct = math.cos(theta)
    s2t = 2.0 * st * ct
    c2t = 2.0 * ct * ct - 1.0
    r = [0.0] * (2 * order)
    t = [0.0] * (2 * order)
    for k in range(order):
        pole_angle = math.pi * float(2 * k + 1) / float(2 * order)
        sin_pa = math.sin(pole_angle)
        cos_pa = math.cos(pole_angle)
        a = 1.0 + s2t * sin_pa
        r[2 * k] = c2t / a
        r[2 * k + 1] = s2t * cos_pa / a
        t[2 * k] = -2.0 * cp * (ct + st * sin_pa) / a
        t[2 * k + 1] = -2.0 * cp * st * cos_pa / a
    den = trinomial_multiply(order, t, r)
    den[1] = den[0]
    den[0] = 1.0
    for k in range(3, 2 * order + 1):
        den[k] = den[2 * k - 2]
    return den[: 2 * order + 1]


def compute_num_coeffs(order: int, lcutoff: float, ucutoff: float, den: Sequence[float]) -> List[float]:
    """Port of ``ComputeNumCoeffs``: numerator scaled to unit gain at the centre frequency."""
    if order > MAX_ORIGINAL_ORDER:
        raise ValueError("the original Numbers[11] table supports order <= 5")
    tco = compute_hp(order)
    num = [0.0] * (2 * order + 1)
    for i in range(order):
        num[2 * i] = tco[i]
        num[2 * i + 1] = 0.0
    num[2 * order] = tco[order]

    cp0 = 2 * 2.0 * math.tan(math.pi * lcutoff / 2.0)
    cp1 = 2 * 2.0 * math.tan(math.pi * ucutoff / 2.0)
    wn = math.sqrt(cp0 * cp1)
    wn = 2 * math.atan2(wn, 4)
    # Original: std::exp(-sqrt(complex<double>(-1,0)) * Wn * Numbers[k]).
    # Apple libc++ evaluates sqrt(-1+0i) as polar(1, atan2(0,-1)/2) =
    # (cos(pi/2), sin(pi/2)) = (6.12e-17, 1), not exactly i, and exp(x+iy) as
    # exp(x)*(cos y + i sin y) (with exp(x) returned unchanged when y == 0).
    # Reproducing that keeps the numerator taps bit-identical to the
    # libc++ build; the effect is ~1e-12 on the taps.
    s_re = 1.0 * math.cos(math.atan2(0.0, -1.0) / 2.0)
    s_im = 1.0 * math.sin(math.atan2(0.0, -1.0) / 2.0)
    kernel_re = []
    for k in range(2 * order + 1):
        x = (-s_re) * wn * float(k)
        y = (-s_im) * wn * float(k)
        kernel_re.append(math.exp(x) if y == 0 else math.exp(x) * math.cos(y))
    _ = cmath  # cmath kept for frequency_response
    b = 0.0
    dsum = 0.0
    for d in range(2 * order + 1):
        b += kernel_re[d] * num[d]
        dsum += kernel_re[d] * den[d]
    for c in range(2 * order + 1):
        num[c] = (num[c] * dsum) / b
    return num


def butter(frequency_bands: Tuple[float, float], order: int) -> Tuple[List[float], List[float]]:
    """Port of ``butter``. Returns ``(b, a)`` = (numerator, denominator).

    Cut-offs are normalised to the Nyquist frequency (as in MATLAB ``butter``).
    The original returned ``z[0] = NumC`` and ``z[1] = DenC``.
    """
    lo, hi = frequency_bands
    den = compute_den_coeffs(order, lo, hi)
    num = compute_num_coeffs(order, lo, hi, den)
    return num, den


def filter_original(ord_: int, a: Sequence[float], b: Sequence[float], x: Sequence[float]) -> List[float]:
    """Port of the original direct-form ``filter`` with zero initial state.

    ``ord_`` is the filter order (2*FILTER_ORDER for the band-pass). Only
    ``len(x)`` outputs are produced; see the module docstring for the original
    one-past-the-end write.
    """
    np_ = len(x)
    y = [0.0] * np_
    if np_ == 0:
        return y
    y[0] = b[0] * x[0]
    for i in range(1, min(ord_ + 1, np_)):
        acc = 0.0
        for j in range(i + 1):
            acc = acc + b[j] * x[i - j]
        for j in range(i):
            acc = acc - a[j + 1] * y[i - j - 1]
        y[i] = acc
    for i in range(ord_ + 1, np_):
        acc = 0.0
        for j in range(ord_ + 1):
            acc = acc + b[j] * x[i - j]
        for j in range(ord_):
            acc = acc - a[j + 1] * y[i - j - 1]
        y[i] = acc
    return y


def frequency_response(b: Sequence[float], a: Sequence[float], w: float) -> complex:
    """H(e^{jw}) for digital angular frequency ``w`` in radians/sample (helper for tests)."""
    z = cmath.exp(-1j * w)
    num = sum(bk * z ** k for k, bk in enumerate(b))
    den = sum(ak * z ** k for k, ak in enumerate(a))
    return num / den
