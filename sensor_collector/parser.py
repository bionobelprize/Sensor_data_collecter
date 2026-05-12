from __future__ import annotations

import json
from datetime import datetime, timezone

from sensor_collector.models import SensorReading


DEVICE_ID_KEYS = ("device_id", "deviceId", "id")
TIMESTAMP_KEYS = ("timestamp", "time", "ts")


def _extract_device_id(payload: dict) -> str:
    for key in DEVICE_ID_KEYS:
        value = payload.get(key)
        if value:
            return str(value)
    raise ValueError("payload missing device_id")


def _extract_timestamp(payload: dict) -> datetime:
    for key in TIMESTAMP_KEYS:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    return datetime.now(tz=timezone.utc)


def _to_float(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("value must be numeric")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("value must be numeric")
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError("value must be numeric") from exc
    raise ValueError("value must be numeric")


def parse_sensor_payload(raw_payload: bytes | str) -> SensorReading:
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8")

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    device_id = _extract_device_id(payload)
    timestamp = _extract_timestamp(payload)

    metrics: dict[str, float] = {}

    # Preferred sensor payload format: {"sensor_type": "...", "value": "..."}
    # The value can be numeric or numeric string.
    sensor_type = payload.get("sensor_type")
    if sensor_type:
        if "value" not in payload:
            raise ValueError("payload missing value for sensor_type")
        metrics[str(sensor_type)] = _to_float(payload.get("value"))

    for key, value in payload.items():
        if key in {*DEVICE_ID_KEYS, *TIMESTAMP_KEYS, "sensor_type", "value"}:
            continue
        if isinstance(value, (int, float)):
            metrics[key] = float(value)

    return SensorReading(device_id=device_id, timestamp=timestamp, metrics=metrics)
