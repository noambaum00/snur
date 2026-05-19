from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

from .config import MicPosition


Point2D = Tuple[float, float]


def rms(signal: Sequence[float]) -> float:
    if not signal:
        return 0.0
    return math.sqrt(sum(x * x for x in signal) / len(signal))


def estimate_delay_seconds(
    signal_a: Sequence[float],
    signal_b: Sequence[float],
    sample_rate_hz: int,
    max_lag_samples: int,
) -> float:
    if len(signal_a) != len(signal_b):
        raise ValueError("Signals must be the same length")
    if not signal_a:
        return 0.0

    best_lag = 0
    best_corr = float("-inf")
    for lag in range(-max_lag_samples, max_lag_samples + 1):
        corr = 0.0
        count = 0
        for i, va in enumerate(signal_a):
            j = i + lag
            if 0 <= j < len(signal_b):
                corr += va * signal_b[j]
                count += 1
        if count > 0:
            corr /= count
            if corr > best_corr:
                best_corr = corr
                best_lag = lag

    return -best_lag / float(sample_rate_hz)


def compute_tdoa_delays(
    frame_by_channel: Dict[int, Sequence[float]],
    channel_order: Sequence[int],
    sample_rate_hz: int,
    max_lag_samples: int,
) -> List[float]:
    reference = frame_by_channel[channel_order[0]]
    delays = [0.0]
    for ch in channel_order[1:]:
        delays.append(
            estimate_delay_seconds(reference, frame_by_channel[ch], sample_rate_hz, max_lag_samples)
        )
    return delays


def _distance(a: Point2D, b: Point2D) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def localize_2d_grid_search(
    mic_positions: Sequence[MicPosition],
    tdoa_delays_s: Sequence[float],
    speed_of_sound_mps: float,
    bounds: Tuple[float, float, float, float],
    step_m: float,
) -> Point2D:
    if len(mic_positions) != len(tdoa_delays_s):
        raise ValueError("Microphone positions and delays length mismatch")
    if len(mic_positions) < 2:
        raise ValueError("At least two microphones are required")

    min_x, max_x, min_y, max_y = bounds
    ref = mic_positions[0]
    best_point = (0.0, 0.0)
    best_error = float("inf")

    x = min_x
    while x <= max_x + 1e-9:
        y = min_y
        while y <= max_y + 1e-9:
            p = (x, y)
            d_ref = _distance(p, ref)
            error = 0.0
            for mic_idx in range(1, len(mic_positions)):
                d_m = _distance(p, mic_positions[mic_idx])
                model_delay = (d_m - d_ref) / speed_of_sound_mps
                diff = model_delay - tdoa_delays_s[mic_idx]
                error += diff * diff
            if error < best_error:
                best_error = error
                best_point = p
            y += step_m
        x += step_m

    return best_point

