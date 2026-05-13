from datetime import datetime, timezone

from sensor_collector.parser import parse_agriculture_topic, parse_sensor_payload


def test_parse_sensor_payload_success() -> None:
    reading = parse_sensor_payload(
        '{"device_id":"dev-1","timestamp":"2026-05-11T12:00:00Z","temperature":25.6,"humidity":40,"co2":520}'
    )

    assert reading.device_id == "dev-1"
    assert reading.timestamp.isoformat() == "2026-05-11T12:00:00+00:00"
    assert reading.metrics["temperature"] == 25.6
    assert reading.metrics["humidity"] == 40.0
    assert reading.metrics["co2"] == 520.0


def test_parse_sensor_payload_invalid_json() -> None:
    try:
        parse_sensor_payload("not-json")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "invalid json payload" in str(exc)


def test_parse_sensor_payload_sensor_type_value_string() -> None:
    reading = parse_sensor_payload('{"device_id":"dev-2","sensor_type":"temperature","value":"24.8"}')

    assert reading.device_id == "dev-2"
    assert reading.metrics["temperature"] == 24.8


def test_parse_sensor_payload_without_timestamp_uses_server_time() -> None:
    before = datetime.now(tz=timezone.utc)
    reading = parse_sensor_payload('{"device_id":"dev-3","sensor_type":"humidity","value":"45"}')
    after = datetime.now(tz=timezone.utc)

    assert before <= reading.timestamp <= after


def test_parse_sensor_payload_sensor_type_without_value() -> None:
    try:
        parse_sensor_payload('{"device_id":"dev-4","sensor_type":"co2"}')
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "missing value" in str(exc)


def test_parse_agriculture_topic_success() -> None:
    topic = "agriculture/agri10086/farm_a/greenhouse/gh01/sensor/th01/telemetry"
    topic_data = parse_agriculture_topic(topic)

    assert topic_data["org_id"] == "agri10086"
    assert topic_data["farm_id"] == "farm_a"
    assert topic_data["region_type"] == "greenhouse"
    assert topic_data["region_id"] == "gh01"
    assert topic_data["device_class"] == "sensor"
    assert topic_data["device_id"] == "th01"
    assert topic_data["data_type"] == "telemetry"


def test_parse_sensor_payload_seq_and_data_object_with_topic() -> None:
    topic = "agriculture/agri10086/farm_a/greenhouse/gh01/sensor/th01/telemetry"
    reading = parse_sensor_payload(
        '{"seq":12345,"timestamp":"2026-05-11T12:00:00Z","data":{"temperature":25.6,"humidity":"40","status":"ok"}}',
        topic=topic,
    )

    assert reading.device_id == "th01"
    assert reading.timestamp.isoformat() == "2026-05-11T12:00:00+00:00"
    assert reading.metrics["seq"] == 12345.0
    assert reading.metrics["temperature"] == 25.6
    assert reading.metrics["humidity"] == 40.0
    assert "status" not in reading.metrics


def test_parse_sensor_payload_seq_and_data_scalar() -> None:
    reading = parse_sensor_payload('{"device_id":"dev-5","seq":7,"data":"1704960503"}')

    assert reading.device_id == "dev-5"
    assert reading.metrics["seq"] == 7.0
    assert reading.metrics["value"] == 1704960503.0


def test_parse_sensor_payload_invalid_agriculture_topic() -> None:
    try:
        parse_sensor_payload('{"device_id":"dev-6","temperature":25.6}', topic="sensors/dev-6")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "topic" in str(exc)
