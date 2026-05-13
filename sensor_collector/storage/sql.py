from __future__ import annotations

import json

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, Text, create_engine
from sqlalchemy.engine import Engine

from sensor_collector.config import DatabaseConfig
from sensor_collector.models import SensorReading
from sensor_collector.storage.base import BaseStorage


class SQLStorage(BaseStorage):
    def __init__(self, cfg: DatabaseConfig) -> None:
        super().__init__(cfg.retry_times, cfg.retry_delay_seconds)
        self._engine: Engine = create_engine(cfg.sql_url, future=True)
        self._metadata = MetaData()
        self._table = Table(
            "sensor_readings",
            self._metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("device_id", String(128), nullable=False, index=True),
            Column("timestamp", DateTime(timezone=True), nullable=False, index=True),
            Column("temperature", Float, nullable=True),
            Column("humidity", Float, nullable=True),
            Column("co2", Float, nullable=True),
            Column("payload", Text, nullable=False),
        )
        self._metadata.create_all(self._engine)

    def _write_once(self, reading: SensorReading) -> None:
        values = {
            "device_id": reading.device_id,
            "timestamp": reading.timestamp,
            "temperature": reading.metrics.get("temperature"),
            "humidity": reading.metrics.get("humidity"),
            "co2": reading.metrics.get("co2"),
            "payload": json.dumps(reading.metrics, ensure_ascii=False),
        }
        with self._engine.begin() as connection:
            connection.execute(self._table.insert().values(**values))

    def close(self) -> None:
        self._engine.dispose()
