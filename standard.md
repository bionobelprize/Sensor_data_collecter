基于我们所有讨论，下面给出**完整的智慧农业MQTT指令集**，包含50个物理量ID表、Topic规范、Payload格式（上行/下行）、以及多区域/多类型扩展方案。

---

## 一、Topic 格式规范（最终版）

```
agriculture/{org_id}/{farm_id}/{region_type}/{region_id}/{device_class}/{device_id}
```

### 字段说明

| 层级 | 说明 | 示例 |
|------|------|------|
| `org_id` | 组织/公司ID | `agri10086` |
| `farm_id` | 农场/生产基地ID | `farm_a` |
| `region_type` | 区域类型 | `greenhouse`, `field`, `orchard`, `pond`, `livestock` |
| `region_id` | 区域编号（同类型内唯一） | `gh01`, `gh02` |
| `device_class` | 设备类别 | `sensor`, `actuator`, `controller`, `gateway` |
| `device_id` | 设备唯一ID（类别内唯一） | `th01`, `valve03` |

### 上行专用后缀（data_type）

| data_type | 用途 | 方向 |
|-----------|------|------|
| `telemetry` | 周期性传感数据 | 上行 |
| `event` | 告警/事件 | 上行 |
| `response` | 对下行指令的响应 | 上行 |
| `status` | 设备状态（心跳/电量） | 上行 |
| `discovery` | 新设备注册 | 上行 |

### 下行专用后缀

| data_type | 用途 | 方向 |
|-----------|------|------|
| `set` | 控制指令 | 下行 |
| `get` | 配置查询 | 下行 |
| `config` | 配置下发 | 下行 |
| `ack` | 对上行数据的确认 | 下行 |

### 完整Topic示例

```
# 温室1号温湿度传感器数据上报
agriculture/agri10086/farm_a/greenhouse/gh01/sensor/th01/telemetry

# 大田B土壤传感器数据上报
agriculture/agri10086/farm_a/field/field_b/sensor/soil03/telemetry

# 池塘2号增氧机控制
agriculture/agri10086/farm_a/pond/pond02/actuator/aerator01/set

# 对所有温室阀门广播（通配符）
agriculture/agri10086/farm_a/greenhouse/+/actuator/+/set
```

---

## 二、上行Payload格式（传感器→网关→平台）




```json
{
  "seq": 12345,
  "data": 1704960503,
}
```

seq: 序列号
data: 具体数据