"""Frame -> green-component reduction, ported from ``UIImage+ImageAverageColor.m``.

The original app captured ``kCVPixelFormatType_32BGRA`` frames at the
``AVCaptureSessionPreset352x288`` preset and called ``averageColorPrecise``,
which sums each channel over every pixel and scales by
``1 / (255 * width * height)``. Byte offset 1 of each BGRA pixel is green.
This updated reduction uses Python double precision for the scale; the
original computes its scale in float32 before assigning it to CGFloat.
Raw-frame results are therefore numerically close, not bit-identical.
"""

from __future__ import annotations

from typing import Tuple


def average_color_precise_bgra(buf: bytes, width: int, height: int,
                               bytes_per_row: int | None = None) -> Tuple[float, float, float]:
    """Return the (red, green, blue) UIColor components in [0, 1].

    Mirrors ``averageColorPrecise``: red = byte 2, green = byte 1, blue = byte 0.
    The original accumulated in 32-bit ``unsigned int``; frames of 352x288
    cannot overflow that, and Python integers cannot overflow at all.
    """
    stride = 4
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if bytes_per_row is None:
        bytes_per_row = width * stride
    if bytes_per_row < width * stride:
        raise ValueError("bytes_per_row must fit every BGRA pixel in a row")
    if len(buf) < bytes_per_row * (height - 1) + width * stride:
        raise ValueError("buffer too small for the given geometry")
    red = green = blue = 0
    for row in range(height):
        base = bytes_per_row * row
        row_bytes = buf[base: base + width * stride]
        blue += sum(row_bytes[0::4])
        green += sum(row_bytes[1::4])
        red += sum(row_bytes[2::4])
    f = 1.0 / (255.0 * width * height)
    return f * red, f * green, f * blue


def green_component_bgra(buf: bytes, width: int, height: int, bytes_per_row: int | None = None) -> float:
    """Green component the original fed into ``Algorithm`` for one frame."""
    return average_color_precise_bgra(buf, width, height, bytes_per_row)[1]
