# 4 传感器标定公式速查
**项目**：BrewXOS · iGEM 2026
**作者**：赵昶瑞
**日期**：2026-08-10 家里蹲配
**适用**：2026-08-11 8 月实机测试 Day 1

---

## 1. pH 传感器（模拟量，DFRobot SEN0161 / 类似）

### 接线
- VCC → 5V
- GND → GND
- Signal → A0 (或 A1)

### 标定（3 点：pH 4 / 7 / 10）
- 准备 pH 4.00, 7.00, 10.00 标准缓冲液（**校准当天新开封**）
- 每个 buffer 泡 1 min，读 5 次 analogRead 取均值
- 记录到 `cal_pH_20260811.csv`

### 公式
- 理想 Nernst slope = 59 mV/pH（25°C）
- Arduino 5V ADC: 1 unit = 4.88 mV
- **3 点线性回归**：
  ```
  slope = (pH10 - pH4) / (ADC_10 - ADC_4)         // 单位: pH/ADC
  offset = 7 - slope * ADC_7
  pH = slope * analogRead + offset
  ```
- **验收标准**：|pH 计算 - pH 实际| < 0.1（三个 buffer 都验）

### 温度补偿
- pH 随温度漂移 ~0.003 pH/°C
- 发酵 37°C 时，offset 校正 = 0.003 × (37-25) = +0.036 pH
- 实测时记得填温度到 CSV

---

## 2. DO 溶解氧传感器（电流型 / 电压型，如 DFRobot SEN0237）

### 接线
- VCC → 5V
- GND → GND
- Signal → A1

### 标定（2 点：空气饱和 + 无氧）
- **空气饱和 (DO = 100%)**：探头暴露空气中 + 小风扇吹 5 min
- **无氧 (DO = 0%)**：探头浸入新配的 Na₂SO₃ 溶液（零氧液）
- 温度补偿：空气饱和 DO 浓度随温度变化

### 温度对照表（mg/L, 1 atm）

| 温度 (°C) | DO 饱和 (mg/L) |
|---|---|
| 25 | 8.25 |
| 30 | 7.56 |
| 35 | 6.95 |
| **37** | **6.72** ← 发酵温度 |
| 40 | 6.41 |

### 公式
```
DO_air_V = analogRead 时的电压 (V)         // 100% 饱和
DO_zero_V = Na2SO3 中电压 (V)              // 0%
DO_mgL = (V_reading - DO_zero_V) / (DO_air_V - DO_zero_V) × DO_sat(T)
```

### 验收
- 空气中读数应稳定 ±0.1 mg/L
- Na₂SO₃ 液中读数 < 0.5 mg/L

---

## 3. DS18B20 温度传感器（数字，单总线）

### 接线
- VCC (红线) → 5V
- GND (黑线) → GND
- DATA (黄线) → D2
- **必须 4.7kΩ 上拉电阻**（DATA ↔ VCC）

### 标定
- DS18B20 出厂校准 ±0.5°C，**理论上不用标**
- 但跟水银温度计对比 3 个温度点（室温 / 37 / 50）做交叉验证
- 记录到 `cal_temp_20260811.csv`

### 公式
- 直接读 Celsius，**不需要公式**
- Arduino 库：`<OneWire.h>` + `<DallasTemperature.h>`
- 采样：每 2s 读一次

### 验收
- |T_DS18B20 - T_水银| < 0.5°C

---

## 4. CO2 传感器（如 MH-Z19B 或 SCD30）

### MH-Z19B 接线（UART 模式）
- VCC → 5V（**必须 5V，不能 3.3V**）
- GND → GND
- TX → D10 (Arduino RX)
- RX → D11 (Arduino TX)

### 标定
- **400 ppm 基线**：户外空气（**通风 5 min 后**）或开窗 5 min
- **1000 ppm 验证**：人呼气 3 次到塑料袋里测
- **零气（可选）**：N₂ 气（实验室没有就跳过）

### 公式
- 直接读 ppm，**不需要公式**
- UART 协议：发 0xFF 0x01 0x86 0x00 0x00 0x00 0x00 0x00 0x79 → 返回 9 字节
- Arduino 库：`<MHZ19.h>`
- 预热时间：**3 分钟**（通电后等 3 min 数据才稳）

### 验收
- 户外空气读数 380-420 ppm
- 室内密闭 5 min 后应 > 600 ppm

---

## 5. 通用接线图（DFRduino Mega2560）

```
                  DFRduino Mega2560
                  ┌──────────────────┐
   pH Sensor ───► A0 │
   DO Sensor ───► A1 │
                  5V │◄─── VCC (4 传感器共享)
                 GND │◄─── GND (4 传感器共享)
  DS18B20 DATA ──► D2 │  + 4.7kΩ 上拉到 5V
  MH-Z19B  TX ──◄ D10 │ (Arduino RX)
  MH-Z19B  RX ──► D11 │ (Arduino TX)
                  D9 │◄─── 加热膜继电器信号
                  D3 │◄─── 蠕动泵 1 (PWM)
                  D5 │◄─── 蠕动泵 2 (PWM)
                  D7 │◄─── LCD RS
                  D8 │◄─── LCD EN
              D4-D8 │   LCD 数据线
                  └──────────────────┘
```

---

## 6. 验收总表

| 传感器 | 验收标准 | 数据记录 CSV |
|---|---|---|
| pH | 3 buffer 误差 < 0.1 | `cal_pH_20260811.csv` |
| DO | 空气 ±0.1 mg/L，Na₂SO₃ < 0.5 | `cal_DO_20260811.csv` |
| DS18B20 | vs 水银 < 0.5°C | `cal_temp_20260811.csv` |
| CO2 | 户外 380-420 ppm | `cal_CO2_20260811.csv` |

---

## 7. 时间表

- **2026-08-10 今晚**：下载 datasheet，备份到 `docs/hardware/datasheets/`
- **2026-08-11 周一**：按本表执行 4 传感器独立标定
- **2026-08-12 周二**：串口 24h 稳定性 + Python 接收落盘
- **2026-08-13 周三**：加热膜 + 蠕动泵 PID 试跑
- **2026-08-14 周四**：水/培养基空白基线 24h

---

## 8. 参考文档下载（如果还没下）

- pH (SEN0161)：https://wiki.dfrobot.com.cn/_SKU_SEN0161_pH_meter_V1
- DO (SEN0237)：https://wiki.dfrobot.com.cn/_SKU_SEN0237_Dissolved_Oxygen_Sensor
- DS18B20：https://www.analog.com/en/products/ds18b20.html (datasheet)
- MH-Z19B：https://www.winsen-sensor.com/product/mh-z19b.html
