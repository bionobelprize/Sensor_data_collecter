from sensor_collector.storage.influx import process_mqtt_message


def test_process_mqtt_telemetry_uses_full_topic_tags() -> None:
    topic = "agriculture/ludong/farm01/lab01/room208/sensor/airtemp01/telemetry"
    payload = {"data": 21.5, "seq": 461, "unit": "celsius"}

    point = process_mqtt_message(topic, payload)
    assert point is not None

    line = point.to_line_protocol()
    assert line.startswith("sensor_data,")
    assert ",org_id=ludong" in line
    assert ",farm_id=farm01" in line
    assert ",region_type=lab01" in line
    assert ",region_id=room208" in line
    assert ",device_class=sensor" in line
    assert ",device_id=airtemp01" in line
    assert ",msg_type=telemetry" in line
    assert ",unit=celsius" in line
    assert " data=21.5" in line
    assert "seq=461" in line


def test_process_mqtt_event_adds_event_tags() -> None:
    topic = "agriculture/ludong/farm01/lab01/room208/sensor/airtemp01/event"
    payload = {"event_type": "overheat", "value": 35.2, "threshold": 30.0}

    point = process_mqtt_message(topic, payload)
    assert point is not None

    line = point.to_line_protocol()
    assert line.startswith("sensor_data,")
    assert ",msg_type=event" in line
    assert ",is_event=true" in line
    assert ",event_type=overheat" in line
    assert " value=35.2" in line
    assert "threshold=30" in line


def test_process_mqtt_set_skipped_when_command_logging_disabled() -> None:
    topic = "agriculture/ludong/farm01/lab01/room208/controller/valve01/set"
    payload = {"command": "open", "duration": 30}

    point = process_mqtt_message(topic, payload, should_log_commands=False)
    assert point is None


def test_process_mqtt_set_written_to_command_log_when_enabled() -> None:
    topic = "agriculture/ludong/farm01/lab01/room208/controller/valve01/set"
    payload = {"command": "open", "duration": 30, "params": {"mode": "timed"}}

    point = process_mqtt_message(topic, payload, should_log_commands=True)
    assert point is not None

    line = point.to_line_protocol()
    assert line.startswith("command_log,")
    assert ",command_type=set" in line
    assert ",msg_type=set" in line
    assert 'command="open"' in line
    assert "duration=30" in line
    assert "params=\"{'mode': 'timed'}\"" in line


def test_process_mqtt_ack_adds_ack_defaults() -> None:
    topic = "agriculture/ludong/farm01/lab01/room208/gateway/gw01/ack"
    payload = {}

    point = process_mqtt_message(topic, payload)
    assert point is not None

    line = point.to_line_protocol()
    assert line.startswith("device_data,")
    assert ",is_ack=true" in line
    assert 'ack_status="received"' in line
