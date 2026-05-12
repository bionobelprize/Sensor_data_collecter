# Sensor Data Collector

多环境传感器 MQTT 数据采集归档服务（Python）。

## 功能特性

- MQTT 客户端常驻运行，支持 Topic 通配符（如 `sensors/#`）统一接入所有传感器数据。
- 自动解析 JSON 报文，提取 `device_id`、时间戳和环境指标（如 temperature/humidity/co2）。
- 存储层可切换：InfluxDB（默认）/ MySQL / SQLite。
- 分层模块化：配置层、MQTT 层、解析层、存储层、日志层。
- 日志按文件滚动切分（10MB * 10 份）并输出到控制台。
- 启动主程序时同时启动 Flask 状态服务，可查看当前运行状态与处理计数。
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

启动后状态接口默认可用：

```bash
curl http://127.0.0.1:5050/
curl http://127.0.0.1:5050/health
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

## MQTT 报文格式要求

程序在订阅到消息后，会按以下逻辑解析：

推荐你的传感器统一使用以下格式：

```json
{
  "device_id": "sensor-001",
  "sensor_type": "temperature",
  "value": "24.5"
}
```

该格式中 `value` 可以是数字，也可以是数字字符串。

- MQTT topic：不要求固定 topic 名称，但必须匹配配置中的订阅通配符（默认 `sensors/#`）。
- Payload 编码：应为 UTF-8 文本。
- Payload 类型：必须是 JSON 对象（`{...}`），不是数组或纯字符串。
- 设备标识：必须包含以下任一字段，作为设备 ID：
  - `device_id`
  - `deviceId`
  - `id`
- 时间字段：可选，支持以下任一字段：
  - `timestamp`
  - `time`
  - `ts`

时间字段解析规则：

- 若为数字（int/float），按 Unix 时间戳（秒）处理。
- 若为字符串，按 ISO 8601 解析（支持 `Z` 结尾）。
- 若未提供时间字段，程序使用服务端接收消息时的 UTC 当前时间。

指标字段（写入数据库的 metrics）规则：

- 除设备 ID 和时间字段外，其它字段中仅 `int/float` 类型会被写入。
- 非数值字段（如字符串、布尔、对象、数组）会被忽略。
- 若提供 `sensor_type` 与 `value`，会写入一条指标：`metrics[sensor_type] = value`。

### 最小可用示例

```json
{
  "device_id": "sensor-001",
  "sensor_type": "temperature",
  "value": "24.5"
}
```

### 常见错误示例

```json
"just-text"
```

错误原因：payload 不是 JSON 对象。

```json
{
  "timestamp": "2026-05-11T12:00:00Z",
  "temperature": 24.5
}
```

错误原因：缺少 `device_id`/`deviceId`/`id`。

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

## 状态服务配置

可在 `config.ini` 中设置：

```ini
[status_server]
enabled = true
host = 127.0.0.1
port = 5050
```

也可通过环境变量覆盖：

- `STATUS_SERVER_ENABLED`
- `STATUS_SERVER_HOST`
- `STATUS_SERVER_PORT`
