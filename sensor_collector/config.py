from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class MQTTConfig:
    broker: str
    port: int
    username: str
    password: str
    topic: str
    client_id: str
    keepalive: int


@dataclass(slots=True)
class DatabaseConfig:
    backend: str
    retry_times: int
    retry_delay_seconds: float
    influx_url: str
    influx_token: str
    influx_org: str
    influx_bucket: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    sqlite_path: str

    @property
    def sql_url(self) -> str:
        if self.backend == "mysql":
            return (
                f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
                f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            )
        return f"sqlite:///{self.sqlite_path}"


@dataclass(slots=True)
class LoggingConfig:
    level: str
    log_dir: str
    log_file: str


@dataclass(slots=True)
class StatusServerConfig:
    enabled: bool
    host: str
    port: int


@dataclass(slots=True)
class AppConfig:
    mqtt: MQTTConfig
    database: DatabaseConfig
    logging: LoggingConfig
    status_server: StatusServerConfig


DEFAULTS = {
    "mqtt": {
        "broker": "127.0.0.1",
        "port": "1883",
        "username": "",
        "password": "",
        "topic": "sensors/#",
        "client_id": "sensor-data-collector",
        "keepalive": "60",
    },
    "database": {
        "backend": "influxdb",
        "retry_times": "3",
        "retry_delay_seconds": "2",
        "influx_url": "http://127.0.0.1:8086",
        "influx_token": "",
        "influx_org": "default-org",
        "influx_bucket": "sensor_data",
        "mysql_host": "127.0.0.1",
        "mysql_port": "3306",
        "mysql_user": "sensor_user",
        "mysql_password": "sensor_pass",
        "mysql_database": "sensor_data",
        "sqlite_path": "data/sensor_data.db",
    },
    "logging": {
        "level": "INFO",
        "log_dir": "logs",
        "log_file": "collector.log",
    },
    "status_server": {
        "enabled": "true",
        "host": "127.0.0.1",
        "port": "5050",
    },
}


ENV_KEY_MAP = {
    "mqtt": {
        "broker": "MQTT_BROKER",
        "port": "MQTT_PORT",
        "username": "MQTT_USERNAME",
        "password": "MQTT_PASSWORD",
        "topic": "MQTT_TOPIC",
        "client_id": "MQTT_CLIENT_ID",
        "keepalive": "MQTT_KEEPALIVE",
    },
    "database": {
        "backend": "DB_BACKEND",
        "retry_times": "DB_RETRY_TIMES",
        "retry_delay_seconds": "DB_RETRY_DELAY_SECONDS",
        "influx_url": "INFLUX_URL",
        "influx_token": "INFLUX_TOKEN",
        "influx_org": "INFLUX_ORG",
        "influx_bucket": "INFLUX_BUCKET",
        "mysql_host": "MYSQL_HOST",
        "mysql_port": "MYSQL_PORT",
        "mysql_user": "MYSQL_USER",
        "mysql_password": "MYSQL_PASSWORD",
        "mysql_database": "MYSQL_DATABASE",
        "sqlite_path": "SQLITE_PATH",
    },
    "logging": {
        "level": "LOG_LEVEL",
        "log_dir": "LOG_DIR",
        "log_file": "LOG_FILE",
    },
    "status_server": {
        "enabled": "STATUS_SERVER_ENABLED",
        "host": "STATUS_SERVER_HOST",
        "port": "STATUS_SERVER_PORT",
    },
}


def load_config(config_path: str = "config.ini", env_file: str = ".env") -> AppConfig:
    load_dotenv(env_file, override=False)

    parser = configparser.ConfigParser()
    parser.read_dict(DEFAULTS)

    cfg = Path(config_path)
    if cfg.exists():
        parser.read(config_path)

    for section, key_mapping in ENV_KEY_MAP.items():
        for option, env_key in key_mapping.items():
            env_val = os.getenv(env_key)
            if env_val is not None:
                parser.set(section, option, env_val)

    db_backend = parser.get("database", "backend").strip().lower()
    if db_backend not in {"influxdb", "mysql", "sqlite"}:
        raise ValueError("database.backend must be one of: influxdb/mysql/sqlite")

    app_cfg = AppConfig(
        mqtt=MQTTConfig(
            broker=parser.get("mqtt", "broker"),
            port=parser.getint("mqtt", "port"),
            username=parser.get("mqtt", "username"),
            password=parser.get("mqtt", "password"),
            topic=parser.get("mqtt", "topic"),
            client_id=parser.get("mqtt", "client_id"),
            keepalive=parser.getint("mqtt", "keepalive"),
        ),
        database=DatabaseConfig(
            backend=db_backend,
            retry_times=parser.getint("database", "retry_times"),
            retry_delay_seconds=parser.getfloat("database", "retry_delay_seconds"),
            influx_url=parser.get("database", "influx_url"),
            influx_token=parser.get("database", "influx_token"),
            influx_org=parser.get("database", "influx_org"),
            influx_bucket=parser.get("database", "influx_bucket"),
            mysql_host=parser.get("database", "mysql_host"),
            mysql_port=parser.getint("database", "mysql_port"),
            mysql_user=parser.get("database", "mysql_user"),
            mysql_password=parser.get("database", "mysql_password"),
            mysql_database=parser.get("database", "mysql_database"),
            sqlite_path=parser.get("database", "sqlite_path"),
        ),
        logging=LoggingConfig(
            level=parser.get("logging", "level"),
            log_dir=parser.get("logging", "log_dir"),
            log_file=parser.get("logging", "log_file"),
        ),
        status_server=StatusServerConfig(
            enabled=parser.getboolean("status_server", "enabled"),
            host=parser.get("status_server", "host"),
            port=parser.getint("status_server", "port"),
        ),
    )

    sqlite_parent = Path(app_cfg.database.sqlite_path).parent
    if app_cfg.database.backend == "sqlite" and str(sqlite_parent) not in {"", "."}:
        sqlite_parent.mkdir(parents=True, exist_ok=True)

    Path(app_cfg.logging.log_dir).mkdir(parents=True, exist_ok=True)
    return app_cfg
