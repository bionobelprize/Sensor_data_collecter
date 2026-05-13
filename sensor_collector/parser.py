from __future__ import annotations

import json
from datetime import datetime, timezone

from sensor_collector.models import SensorReading


DEVICE_ID_KEYS = ("device_id", "deviceId", "id")
TIMESTAMP_KEYS = ("timestamp", "time", "ts")

AGRI_TOPIC_PREFIX = "agriculture"
AGRI_TOPIC_PARTS = 8


def parse_agriculture_topic(topic: str) -> dict[str, str]:
    parts = topic.split("/")
    if len(parts) != AGRI_TOPIC_PARTS:
        raise ValueError("topic must contain 8 parts")
    if parts[0] != AGRI_TOPIC_PREFIX:
        raise ValueError("topic must start with agriculture")

    keys = (
        "prefix",
        "org_id",
        "farm_id",
        "region_type",
        "region_id",
        "device_class",
        "device_id",
        "data_type",
    )

    topic_data = dict(zip(keys, parts, strict=False))
    for key in keys:
        if not topic_data.get(key):
            raise ValueError(f"topic missing {key}")
    return topic_data


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


def _extract_data_metrics(data_value: object) -> dict[str, float]:
    metrics: dict[str, float] = {}

    if isinstance(data_value, dict):
        for key, value in data_value.items():
            try:
                metrics[str(key)] = _to_float(value)
            except ValueError:
                continue
        return metrics

    try:
        metrics["value"] = _to_float(data_value)
    except ValueError:
        pass
    return metrics


def parse_sensor_payload(raw_payload: bytes | str, topic: str | None = None) -> SensorReading:
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8")

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    topic_data: dict[str, str] = {}
    if topic:
        topic_data = parse_agriculture_topic(topic)

    device_id = topic_data.get("device_id") or _extract_device_id(payload)
    timestamp = _extract_timestamp(payload)

    metrics: dict[str, float] = {}

    if "seq" in payload:
        metrics["seq"] = _to_float(payload.get("seq"))

    if "data" in payload:
        metrics.update(_extract_data_metrics(payload.get("data")))

    # Preferred sensor payload format: {"sensor_type": "...", "value": "..."}
    # The value can be numeric or numeric string.
    sensor_type = payload.get("sensor_type")
    if sensor_type:
        if "value" not in payload:
            raise ValueError("payload missing value for sensor_type")
        metrics[str(sensor_type)] = _to_float(payload.get("value"))

    for key, value in payload.items():
        if key in {*DEVICE_ID_KEYS, *TIMESTAMP_KEYS, "sensor_type", "value", "seq", "data"}:
            continue
        try:
            metrics[key] = _to_float(value)
        except ValueError:
            continue

    return SensorReading(device_id=device_id, timestamp=timestamp, metrics=metrics)
