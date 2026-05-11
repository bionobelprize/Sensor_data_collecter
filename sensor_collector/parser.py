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
    for key, value in payload.items():
        if key in {*DEVICE_ID_KEYS, *TIMESTAMP_KEYS}:
            continue
        if isinstance(value, (int, float)):
            metrics[key] = float(value)

    return SensorReading(device_id=device_id, timestamp=timestamp, metrics=metrics)
