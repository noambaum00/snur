from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Dict, List, Sequence

from .config import AppConfig, MicPosition


def _distance(p1: MicPosition, p2: MicPosition) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


class MCP3008AudioReader:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._spi = None
        self._simulation_phase = 0.0
        self._sim_source = (0.9, 0.2)
        if not config.simulate:
            try:
                import spidev  # type: ignore

                self._spi = spidev.SpiDev()
                self._spi.open(config.spi_bus, config.spi_device)
                self._spi.max_speed_hz = 1_350_000
            except Exception as exc:
                raise RuntimeError(
                    "Failed to initialize MCP3008 over SPI. Use simulate=true to run without hardware."
                ) from exc

    def read_frame(self) -> Dict[int, List[float]]:
        if self.config.simulate:
            return self._read_simulated_frame()
        return self._read_hardware_frame()

    def _read_hardware_channel(self, channel: int) -> int:
        assert self._spi is not None
        command = [1, (8 + channel) << 4, 0]
        response = self._spi.xfer2(command)
        return ((response[1] & 3) << 8) | response[2]

    def _read_hardware_frame(self) -> Dict[int, List[float]]:
        result: Dict[int, List[float]] = {ch: [] for ch in self.config.channels}
        for _ in range(self.config.frame_size):
            for ch in self.config.channels:
                raw = self._read_hardware_channel(ch)
                normalized = (raw - 512.0) / 512.0
                result[ch].append(normalized)
        return result

    def _simulated_channel_delay_s(self, mic_pos: MicPosition, all_positions: Sequence[MicPosition]) -> float:
        ref = all_positions[0]
        d_ref = _distance(self._sim_source, ref)
        d_mic = _distance(self._sim_source, mic_pos)
        return (d_mic - d_ref) / self.config.speed_of_sound_mps

    def _read_simulated_frame(self) -> Dict[int, List[float]]:
        result: Dict[int, List[float]] = {}
        freq_hz = 900.0
        mic_positions = self.config.mic_positions
        for idx, ch in enumerate(self.config.channels):
            delay = self._simulated_channel_delay_s(mic_positions[idx], mic_positions)
            phase_shift = -2.0 * math.pi * freq_hz * delay
            samples: List[float] = []
            for n in range(self.config.frame_size):
                t = (self._simulation_phase + n) / self.config.sample_rate_hz
                sample = math.sin(2.0 * math.pi * freq_hz * t + phase_shift)
                sample += random.uniform(-0.05, 0.05)
                samples.append(sample)
            result[ch] = samples
        self._simulation_phase += self.config.frame_size
        return result


@dataclass
class Diagnostics:
    levels: Dict[int, float]
    delays_s: List[float]

