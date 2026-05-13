from __future__ import annotations

import argparse
import signal
import sys

from sensor_collector.config import load_config
from sensor_collector.logger import setup_logging
from sensor_collector.mqtt_client import MQTTCollectorService
from sensor_collector.status import RuntimeStatus
from sensor_collector.status_server import start_status_server
from sensor_collector.storage import create_storage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MQTT sensor data collector")
    parser.add_argument("--config", default="config.ini", help="Path to config.ini")
    parser.add_argument("--env-file", default=".env", help="Path to .env")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Load config and initialize storage once, then exit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(config_path=args.config, env_file=args.env_file)
    logger = setup_logging(cfg.logging)
    storage = create_storage(cfg.database)
    runtime_status = RuntimeStatus()

    if args.check:
        logger.info("Configuration and storage initialization successful")
        storage.close()
        return 0

    if cfg.status_server.enabled:
        start_status_server(
            status=runtime_status,
            host=cfg.status_server.host,
            port=cfg.status_server.port,
            logger=logger,
        )

    service = MQTTCollectorService(cfg.mqtt, storage, logger, status=runtime_status)
    runtime_status.mark_service_running()

    def _shutdown(signal_number, stack_frame) -> None:  # noqa: ANN001
        logger.info("Received signal %s, shutting down", signal_number)
        runtime_status.mark_service_stopped()
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        service.start()
    finally:
        runtime_status.mark_service_stopped()
        storage.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
