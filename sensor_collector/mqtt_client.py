from __future__ import annotations

import logging

import paho.mqtt.client as mqtt

from sensor_collector.config import MQTTConfig
from sensor_collector.parser import parse_sensor_payload
from sensor_collector.status import RuntimeStatus
from sensor_collector.storage.base import BaseStorage


class MQTTCollectorService:
    def __init__(
        self,
        cfg: MQTTConfig,
        storage: BaseStorage,
        logger: logging.Logger,
        status: RuntimeStatus | None = None,
    ) -> None:
        self.cfg = cfg
        self.storage = storage
        self.logger = logger
        self.status = status

        self.client = mqtt.Client(client_id=cfg.client_id, clean_session=True)
        if cfg.username:
            self.client.username_pw_set(cfg.username, cfg.password)

        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client: mqtt.Client, userdata, flags, result_code: int) -> None:  # noqa: ANN001
        if result_code == mqtt.CONNACK_ACCEPTED:
            self.logger.info("MQTT connected to %s:%s", self.cfg.broker, self.cfg.port)
            if self.status is not None:
                self.status.mark_mqtt_connected()
            client.subscribe(self.cfg.topic)
            self.logger.info("Subscribed topic wildcard: %s", self.cfg.topic)
        else:
            self.logger.error("MQTT connect failed with code: %s", result_code)

    def _on_disconnect(self, client: mqtt.Client, userdata, result_code: int) -> None:  # noqa: ANN001
        if self.status is not None:
            self.status.mark_mqtt_disconnected()
        if result_code != 0:
            self.logger.warning("MQTT disconnected unexpectedly, auto reconnecting...")
        else:
            self.logger.info("MQTT disconnected")

    def _on_message(self, client: mqtt.Client, userdata, message: mqtt.MQTTMessage) -> None:  # noqa: ANN001
        payload_text = message.payload.decode("utf-8", errors="replace")
        self.logger.info("Received topic=%s payload=%s", message.topic, payload_text)
        if self.status is not None:
            self.status.mark_message_received(message.topic)

        try:
            reading = parse_sensor_payload(payload_text, topic=message.topic)
            self.storage.write(reading)
            if self.status is not None:
                self.status.mark_message_stored()
            self.logger.info(
                "Stored reading device_id=%s timestamp=%s metrics=%s",
                reading.device_id,
                reading.timestamp.isoformat(),
                reading.metrics,
            )
        except ValueError as exc:
            if self.status is not None:
                self.status.mark_parse_error(str(exc))
            self.logger.error("Payload parse error topic=%s error=%s", message.topic, exc)
        except Exception as exc:  # noqa: BLE001
            if self.status is not None:
                self.status.mark_storage_error(str(exc))
            self.logger.exception("Storage write failed topic=%s error=%s", message.topic, exc)

    def start(self) -> None:
        self.logger.info("Starting MQTT collector service")
        self.client.connect(self.cfg.broker, self.cfg.port, self.cfg.keepalive)
        self.client.loop_forever(retry_first_connection=True)

    def stop(self) -> None:
        self.client.disconnect()
        self.storage.close()
