from sensor_collector.config import DatabaseConfig
from sensor_collector.storage.base import BaseStorage
from sensor_collector.storage.influx import InfluxStorage
from sensor_collector.storage.sql import SQLStorage


def create_storage(cfg: DatabaseConfig) -> BaseStorage:
    if cfg.backend == "influxdb":
        return InfluxStorage(cfg)
    if cfg.backend in {"mysql", "sqlite"}:
        return SQLStorage(cfg)
    raise ValueError(f"Unsupported database backend: {cfg.backend}")
