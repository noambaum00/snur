from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import threading
import time
from typing import Dict, Optional

from .audio import MCP3008AudioReader
from .config import AppConfig
from .localization import compute_tdoa_delays, localize_2d_grid_search, rms


@dataclass
class LocalizationSnapshot:
    timestamp: str
    x: float
    y: float
    diagnostics: Dict[str, object]


class SoundLocalizationService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._audio_reader = MCP3008AudioReader(config)
        self._lock = threading.Lock()
        self._latest: Optional[LocalizationSnapshot] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger("snur.localization")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def latest(self) -> Optional[LocalizationSnapshot]:
        with self._lock:
            return self._latest

    def _run_loop(self) -> None:
        max_lag_samples = max(1, int(0.001 * self._config.sample_rate_hz))
        while not self._stop.is_set():
            frame = self._audio_reader.read_frame()
            delays = compute_tdoa_delays(
                frame_by_channel=frame,
                channel_order=self._config.channels,
                sample_rate_hz=self._config.sample_rate_hz,
                max_lag_samples=max_lag_samples,
            )
            corrected_delays = [
                d - self._config.calibration_offsets_s[i] for i, d in enumerate(delays)
            ]
            pos = localize_2d_grid_search(
                mic_positions=self._config.mic_positions,
                tdoa_delays_s=corrected_delays,
                speed_of_sound_mps=self._config.speed_of_sound_mps,
                bounds=self._config.search_bounds,
                step_m=self._config.search_step_m,
            )

            levels = {str(ch): rms(frame[ch]) for ch in self._config.channels}
            snapshot = LocalizationSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                x=pos[0],
                y=pos[1],
                diagnostics={"levels": levels, "delays_s": corrected_delays},
            )
            with self._lock:
                self._latest = snapshot

            self._logger.info(
                "Localization x=%.3f y=%.3f delays=%s levels=%s",
                snapshot.x,
                snapshot.y,
                corrected_delays,
                levels,
            )
            time.sleep(self._config.frame_size / float(self._config.sample_rate_hz))

