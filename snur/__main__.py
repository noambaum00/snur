from __future__ import annotations

import argparse
import logging

from .config import load_config
from .service import SoundLocalizationService
from .web import run_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="snur sound localization service")
    parser.add_argument("--config", type=str, default=None, help="Path to JSON config file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    service = SoundLocalizationService(cfg)
    service.start()
    try:
        run_server(cfg.ui_bind_host, cfg.ui_bind_port, service)
    finally:
        service.stop()


if __name__ == "__main__":
    main()

