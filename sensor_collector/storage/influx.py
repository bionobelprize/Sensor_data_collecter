from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision

from sensor_collector.config import DatabaseConfig
from sensor_collector.models import SensorReading
from sensor_collector.storage.base import BaseStorage


TOPIC_PREFIX = "agriculture"
TOPIC_PARTS = 8
LOW_CARDINALITY_TAG_KEYS = {"status", "unit", "alert_level"}
COMMAND_MESSAGE_TYPES = {"set", "get"}


@dataclass(frozen=True, slots=True)
class TopicMetadata:
    org_id: str
    farm_id: str
    region_type: str
    region_id: str
    device_class: str
    device_id: str
    suffix: str


def _parse_topic(topic: str) -> TopicMetadata:
    parts = topic.split("/")
    if len(parts) != TOPIC_PARTS:
        raise ValueError(f"Invalid topic format: {topic}")
    if parts[0] != TOPIC_PREFIX:
        raise ValueError(f"Invalid topic prefix: {topic}")

    _, org_id, farm_id, region_type, region_id, device_class, device_id, suffix = parts
    values = {
        "org_id": org_id,
        "farm_id": farm_id,
        "region_type": region_type,
        "region_id": region_id,
        "device_class": device_class,
        "device_id": device_id,
        "suffix": suffix,
    }
    for key, value in values.items():
        if not value:
            raise ValueError(f"topic missing {key}: {topic}")

    return TopicMetadata(**values)


def _determine_measurement(device_class: str, suffix: str, should_log_commands: bool) -> str | None:
    if suffix in COMMAND_MESSAGE_TYPES and not should_log_commands:
        return None
    if suffix in COMMAND_MESSAGE_TYPES and should_log_commands:
        return "command_log"

    if device_class == "sensor":
        if suffix in {"telemetry", "event"}:
            return "sensor_data"
        return "sensor_control"
    if device_class == "controller":
        return "controller_data"
    return "device_data"


def process_mqtt_message(topic: str, payload: dict, *, should_log_commands: bool = False) -> Point | None:
    """Convert one MQTT message into an InfluxDB Point.

    Returns None when message type should be skipped (for example set/get when command logging is off).
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    topic_meta = _parse_topic(topic)
    measurement = _determine_measurement(topic_meta.device_class, topic_meta.suffix, should_log_commands)
    if measurement is None:
        return None

    point = (
        Point(measurement)
        .tag("org_id", topic_meta.org_id)
        .tag("farm_id", topic_meta.farm_id)
        .tag("region_type", topic_meta.region_type)
        .tag("region_id", topic_meta.region_id)
        .tag("device_class", topic_meta.device_class)
        .tag("device_id", topic_meta.device_id)
        .tag("msg_type", topic_meta.suffix)
    )

    if topic_meta.suffix == "event":
        point.tag("is_event", "true")
        event_type = payload.get("event_type")
        if isinstance(event_type, str) and event_type:
            point.tag("event_type", event_type)

    if topic_meta.suffix == "response":
        point.tag("is_response", "true")
        if "code" in payload:
            code = payload.get("code")
            if isinstance(code, bool):
                point.field("response_code", code)
            elif isinstance(code, (int, float)):
                point.field("response_code", float(code))
            elif isinstance(code, str):
                try:
                    point.field("response_code", float(code))
                except ValueError:
                    point.field("response_code", code)

    if topic_meta.suffix == "ack":
        point.tag("is_ack", "true")
        ack_status = payload.get("status", "received")
        point.field("ack_status", str(ack_status))

    if topic_meta.suffix in COMMAND_MESSAGE_TYPES and should_log_commands:
        point.tag("command_type", topic_meta.suffix)
        point.field("command", str(payload.get("command", "")))
        point.field("params", str(payload.get("params", {})))

    for key, value in payload.items():
        if topic_meta.suffix == "event" and key == "event_type":
            continue
        if topic_meta.suffix == "response" and key == "code":
            continue

        if isinstance(value, bool):
            point.field(key, value)
        elif isinstance(value, (int, float)):
            point.field(key, float(value))
        elif isinstance(value, str):
            if key in LOW_CARDINALITY_TAG_KEYS:
                point.tag(key, value)
            else:
                point.field(key, value)

    # Keep server receive time as the source of truth for timestamps.
    point.time(datetime.now(timezone.utc), WritePrecision.NS)
    return point


class InfluxStorage(BaseStorage):
    def __init__(self, cfg: DatabaseConfig) -> None:
        super().__init__(cfg.retry_times, cfg.retry_delay_seconds)
        self._bucket = cfg.influx_bucket
        self._org = cfg.influx_org
        self._log_commands = cfg.log_commands
        self._client = InfluxDBClient(url=cfg.influx_url, token=cfg.influx_token, org=cfg.influx_org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def _write_once(self, reading: SensorReading) -> None:
        point = Point("sensor_data").tag("device_id", reading.device_id).time(reading.timestamp)
        for key, value in reading.metrics.items():
            point.field(key, value)
        self._write_api.write(bucket=self._bucket, org=self._org, record=point)

    def write_mqtt_message(self, topic: str, payload: dict) -> bool:
        point = process_mqtt_message(topic, payload, should_log_commands=self._log_commands)
        if point is None:
            return False

        last_error: Exception | None = None
        for attempt in range(1, self.retry_times + 1):
            try:
                self._write_api.write(bucket=self._bucket, org=self._org, record=point)
                return True
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.retry_times:
                    time.sleep(self.retry_delay_seconds)

        if last_error:
            raise last_error
        return False

    def close(self) -> None:
        self._client.close()
