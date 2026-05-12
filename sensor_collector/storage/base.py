from __future__ import annotations

import time
from abc import ABC, abstractmethod

from sensor_collector.models import SensorReading


class BaseStorage(ABC):
    def __init__(self, retry_times: int, retry_delay_seconds: float) -> None:
        self.retry_times = max(1, retry_times)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)

    def write(self, reading: SensorReading) -> None:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_times + 1):
            try:
                self._write_once(reading)
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.retry_times:
                    time.sleep(self.retry_delay_seconds)
        if last_error:
            raise last_error

    @abstractmethod
    def _write_once(self, reading: SensorReading) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
