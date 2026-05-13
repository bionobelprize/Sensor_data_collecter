from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock


@dataclass(slots=True)
class RuntimeStatus:
    _lock: Lock = field(default_factory=Lock)
    started_at: str = field(default_factory=lambda: _utc_now_iso())
    service_state: str = "initializing"
    mqtt_connected: bool = False
    last_message_at: str | None = None
    last_message_topic: str | None = None
    messages_received: int = 0
    messages_stored: int = 0
    parse_errors: int = 0
    storage_errors: int = 0
    last_error: str | None = None

    def mark_service_running(self) -> None:
        with self._lock:
            self.service_state = "running"
            self.last_error = None

    def mark_service_stopped(self) -> None:
        with self._lock:
            self.service_state = "stopped"
            self.mqtt_connected = False

    def mark_mqtt_connected(self) -> None:
        with self._lock:
            self.mqtt_connected = True

    def mark_mqtt_disconnected(self) -> None:
        with self._lock:
            self.mqtt_connected = False

    def mark_message_received(self, topic: str) -> None:
        with self._lock:
            self.messages_received += 1
            self.last_message_topic = topic
            self.last_message_at = _utc_now_iso()

    def mark_message_stored(self) -> None:
        with self._lock:
            self.messages_stored += 1

    def mark_parse_error(self, error: str) -> None:
        with self._lock:
            self.parse_errors += 1
            self.last_error = error

    def mark_storage_error(self, error: str) -> None:
        with self._lock:
            self.storage_errors += 1
            self.last_error = error

    def snapshot(self) -> dict[str, str | int | bool | None]:
        with self._lock:
            return {
                "started_at": self.started_at,
                "service_state": self.service_state,
                "mqtt_connected": self.mqtt_connected,
                "last_message_at": self.last_message_at,
                "last_message_topic": self.last_message_topic,
                "messages_received": self.messages_received,
                "messages_stored": self.messages_stored,
                "parse_errors": self.parse_errors,
                "storage_errors": self.storage_errors,
                "last_error": self.last_error,
            }


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
