from sensor_collector.parser import parse_sensor_payload


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
