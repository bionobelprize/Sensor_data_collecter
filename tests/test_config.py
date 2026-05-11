from pathlib import Path

from sensor_collector.config import load_config


def test_load_config_env_override(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    cfg_file = tmp_path / "config.ini"
    cfg_file.write_text(
        """
[mqtt]
broker=10.0.0.1
port=1883

[database]
backend=sqlite
sqlite_path=data/file.db

[logging]
level=INFO
log_dir=logs
log_file=test.log
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("MQTT_BROKER", "mqtt.example.com")
    config = load_config(str(cfg_file), env_file=str(tmp_path / ".env"))
    assert config.mqtt.broker == "mqtt.example.com"
    assert config.database.backend == "sqlite"
