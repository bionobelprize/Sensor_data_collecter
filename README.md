# Sensor Data Collector

多环境传感器 MQTT 数据采集归档服务（Python）。

## 功能特性

- MQTT 客户端常驻运行，支持 Topic 通配符（如 `sensors/#`）统一接入所有传感器数据。
- 自动解析 JSON 报文，提取 `device_id`、时间戳和环境指标（如 temperature/humidity/co2）。
- 存储层可切换：InfluxDB（默认）/ MySQL / SQLite。
- 分层模块化：配置层、MQTT 层、解析层、存储层、日志层。
- 日志按文件滚动切分（10MB * 10 份）并输出到控制台。
- 可靠性保障：MQTT 自动重连、报文格式容错、数据库写入失败重试。
- 支持通过 `config.ini` 和 `.env` 配置，无需改代码。
- 支持 Linux systemd 守护进程部署。

## 项目结构

```text
sensor_data_collector/
├── sensor_collector/
│   ├── __main__.py
│   ├── config.py
│   ├── logger.py
│   ├── main.py
│   ├── models.py
│   ├── mqtt_client.py
│   ├── parser.py
│   └── storage/
│       ├── __init__.py
│       ├── base.py
│       ├── influx.py
│       └── sql.py
├── tests/
│   ├── test_config.py
│   ├── test_parser.py
│   └── test_storage_factory.py
├── config.ini.example
├── .env.example
├── requirements.txt
└── systemd/sensor-collector.service
```

## 快速开始

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 准备配置文件：

```bash
cp config.ini.example config.ini
cp .env.example .env
```

3. 按需修改 MQTT 与数据库参数。

4. 启动服务：

```bash
python -m sensor_collector.main --config config.ini --env-file .env
```

5. 配置检查（不启动订阅）：

```bash
python -m sensor_collector.main --config config.ini --env-file .env --check
```

## 报文格式示例

```json
{
  "device_id": "sensor-001",
  "timestamp": "2026-05-11T12:00:00Z",
  "temperature": 24.5,
  "humidity": 45.2,
  "co2": 580
}
```

## Linux systemd 部署

1. 拷贝项目到 `/opt/sensor_data_collector`。
2. 修改 `config.ini` 和 `.env`。
3. 安装服务文件：

```bash
sudo cp systemd/sensor-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sensor-collector
sudo systemctl start sensor-collector
```

4. 查看运行状态：

```bash
sudo systemctl status sensor-collector
sudo journalctl -u sensor-collector -f
```

## 测试

```bash
pytest tests -q
```
