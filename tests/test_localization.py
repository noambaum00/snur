import math
import unittest

from snur.localization import estimate_delay_seconds, localize_2d_grid_search


class LocalizationTests(unittest.TestCase):
    def test_estimate_delay_seconds_zero_for_identical_signals(self) -> None:
        signal = [math.sin(2 * math.pi * 0.1 * i) for i in range(128)]
        delay = estimate_delay_seconds(signal, signal, sample_rate_hz=8000, max_lag_samples=8)
        self.assertAlmostEqual(delay, 0.0, places=6)

    def test_localize_grid_search_returns_expected_point(self) -> None:
        mics = [(0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2)]
        source = (0.6, 0.4)
        c = 343.0

        def d(a, b):
            return math.hypot(a[0] - b[0], a[1] - b[1])

        ref = d(source, mics[0])
        delays = [0.0]
        for i in range(1, 4):
            delays.append((d(source, mics[i]) - ref) / c)

        got = localize_2d_grid_search(
            mic_positions=mics,
            tdoa_delays_s=delays,
            speed_of_sound_mps=c,
            bounds=(-1.0, 1.0, -1.0, 1.0),
            step_m=0.02,
        )
        self.assertAlmostEqual(got[0], source[0], delta=0.06)
        self.assertAlmostEqual(got[1], source[1], delta=0.06)


if __name__ == "__main__":
    unittest.main()

