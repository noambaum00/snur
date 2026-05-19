from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from typing import List, Sequence, Tuple


MicPosition = Tuple[float, float]


@dataclass
class AppConfig:
    sample_rate_hz: int = 8_000
    frame_size: int = 256
    speed_of_sound_mps: float = 343.0
    mic_positions: List[MicPosition] = field(
        default_factory=lambda: [
            (0.0, 0.0),
            (0.2, 0.0),
            (0.2, 0.2),
            (0.0, 0.2),
        ]
    )
    search_bounds: Tuple[float, float, float, float] = (-1.5, 1.5, -1.5, 1.5)
    search_step_m: float = 0.05
    channels: Sequence[int] = (0, 1, 2, 3)
    spi_bus: int = 0
    spi_device: int = 0
    simulate: bool = True
    ui_bind_host: str = "0.0.0.0"
    ui_bind_port: int = 8080
    calibration_offsets_s: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])


def _as_tuple_pair_list(raw_positions: Sequence[Sequence[float]]) -> List[MicPosition]:
    return [(float(p[0]), float(p[1])) for p in raw_positions]


def load_config(path: str | None = None) -> AppConfig:
    cfg = AppConfig()
    config_path = path or os.getenv("SNUR_CONFIG")
    if config_path and Path(config_path).exists():
        raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
        if "sample_rate_hz" in raw:
            cfg.sample_rate_hz = int(raw["sample_rate_hz"])
        if "frame_size" in raw:
            cfg.frame_size = int(raw["frame_size"])
        if "speed_of_sound_mps" in raw:
            cfg.speed_of_sound_mps = float(raw["speed_of_sound_mps"])
        if "mic_positions" in raw:
            cfg.mic_positions = _as_tuple_pair_list(raw["mic_positions"])
        if "search_bounds" in raw:
            cfg.search_bounds = tuple(float(x) for x in raw["search_bounds"])  # type: ignore[assignment]
        if "search_step_m" in raw:
            cfg.search_step_m = float(raw["search_step_m"])
        if "channels" in raw:
            cfg.channels = tuple(int(c) for c in raw["channels"])
        if "spi_bus" in raw:
            cfg.spi_bus = int(raw["spi_bus"])
        if "spi_device" in raw:
            cfg.spi_device = int(raw["spi_device"])
        if "simulate" in raw:
            cfg.simulate = bool(raw["simulate"])
        if "ui_bind_host" in raw:
            cfg.ui_bind_host = str(raw["ui_bind_host"])
        if "ui_bind_port" in raw:
            cfg.ui_bind_port = int(raw["ui_bind_port"])
        if "calibration_offsets_s" in raw:
            cfg.calibration_offsets_s = [float(x) for x in raw["calibration_offsets_s"]]
    return cfg

