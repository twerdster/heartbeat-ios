"""Modern, dependency-free port of the HeartBeat (2013) green-plane pulse algorithm.

See ``updated/README.md`` for scope, fidelity checks and limitations.
This is a student research prototype port, not a medical device.
"""

from .algorithm import HeartbeatAlgorithm, FrameTrace, run_on_green_components, ORIGINAL_QUIRKS
from .butterworth import butter, filter_original, frequency_response
from .frames import average_color_precise_bgra, green_component_bgra

__all__ = [
    "HeartbeatAlgorithm", "FrameTrace", "run_on_green_components", "ORIGINAL_QUIRKS",
    "butter", "filter_original", "frequency_response",
    "average_color_precise_bgra", "green_component_bgra",
]
