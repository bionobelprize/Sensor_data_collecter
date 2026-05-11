from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SensorReading:
    device_id: str
    timestamp: datetime
    metrics: dict[str, float]
