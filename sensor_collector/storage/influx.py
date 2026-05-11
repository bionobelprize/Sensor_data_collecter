from __future__ import annotations

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from sensor_collector.config import DatabaseConfig
from sensor_collector.models import SensorReading
from sensor_collector.storage.base import BaseStorage


class InfluxStorage(BaseStorage):
    def __init__(self, cfg: DatabaseConfig) -> None:
        super().__init__(cfg.retry_times, cfg.retry_delay_seconds)
        self._bucket = cfg.influx_bucket
        self._org = cfg.influx_org
        self._client = InfluxDBClient(url=cfg.influx_url, token=cfg.influx_token, org=cfg.influx_org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def _write_once(self, reading: SensorReading) -> None:
        point = Point("sensor_data").tag("device_id", reading.device_id).time(reading.timestamp)
        for key, value in reading.metrics.items():
            point.field(key, value)
        self._write_api.write(bucket=self._bucket, org=self._org, record=point)

    def close(self) -> None:
        self._client.close()
