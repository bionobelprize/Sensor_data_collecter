from sensor_collector.config import DatabaseConfig
from sensor_collector.storage import create_storage
from sensor_collector.storage.influx import InfluxStorage
from sensor_collector.storage.sql import SQLStorage


def _base_db_cfg(backend: str) -> DatabaseConfig:
    return DatabaseConfig(
        backend=backend,
        retry_times=2,
        retry_delay_seconds=0.1,
        influx_url="http://localhost:8086",
        influx_token="token",
        influx_org="org",
        influx_bucket="bucket",
        log_commands=False,
        mysql_host="localhost",
        mysql_port=3306,
        mysql_user="root",
        mysql_password="root",
        mysql_database="sensor_data",
        sqlite_path=":memory:",
    )


def test_create_sqlite_storage() -> None:
    storage = create_storage(_base_db_cfg("sqlite"))
    assert isinstance(storage, SQLStorage)
    storage.close()


def test_create_influx_storage() -> None:
    storage = create_storage(_base_db_cfg("influxdb"))
    assert isinstance(storage, InfluxStorage)
    storage.close()
