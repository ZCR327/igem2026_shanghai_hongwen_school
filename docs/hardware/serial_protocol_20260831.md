# Touch Screen ↔ Arduino Serial Protocol (v0.2, 2026-08-31)

## Overview

USART HMI 触控屏 ↔ DFRduino Mega2560 通过 **Serial1 (TX/RX, 9600 baud)** 通信。
触控屏按下按钮后发送单字符 ASCII 指令，Arduino 收到后触发对应继电器动作。

| 参数 | 值 |
|------|---|
| 端口 | Serial1 (D18 TX1 / D19 RX1) |
| 波特率 | **9600**（锁死，触控屏硬件固定） |
| 字符编码 | ASCII（单字符） |
| 数据位 | 8 |
| 校验 | None |
| 停止位 | 1 |

## v0.2 协议（8.31 老师改版，**最新**）

来源：`桌面/宏文装置程序0831.mpcode` (Mind+ 8.31 13:58)

| 触控屏字符 | 继电器动作 | 引脚 | 含义 |
|-----------|----------|------|------|
| `a` | Open  | PIN 43 | 加热膜开 |
| `b` | Close | PIN 43 | 加热膜关 |
| `c` | Open  | PIN 41 | 蠕动泵 A 开 |
| `d` | Close | PIN 41 | 蠕动泵 A 关 |
| `e` | Open  | PIN 42 | 蠕动泵 B 开 |
| `f` | Close | PIN 42 | 蠕动泵 B 关 |
| `g` | Open  | PIN 44 | 搅拌电机开 |
| `h` | Open  | PIN 45 | 备用气泵开 |
| `i` | Close | PIN 44 + PIN 45 | 组合键：搅拌电机 + 备用气泵 **一起关** |

### 设计观察

- **5 个物理继电器**（PIN 41/42/43/44/45）对应 5 个硬件负载
- **完全对称的"开/关"对**：PIN 41/42/43 各有独立开/关字符
- **PIN 44 / PIN 45 不对称**：只有独立"开"字符（`g`/`h`），关闭只能通过组合键 `i`
- **`i` 组合键**：评委看到会问 —— 老师的设计意图可能是"一键全停"，避免误关单个

### 5 路继电器的硬件映射（待标定）

> 8.31 录制时老师未明示 5 路 PIN 各接什么。下列为推断 + 待验证：

| PIN | 推断负载 | 验证方式 |
|-----|---------|---------|
| 41 | 蠕动泵 A（底物进料） | 触摸 c/d 听声音 |
| 42 | 蠕动泵 B（XOS 出料） | 触摸 e/f 听声音 |
| 43 | 加热膜 | 触摸 a 后看温度上升 |
| 44 | 搅拌电机 | 触摸 g 看搅拌转动 |
| 45 | 备用气泵 / 通气阀 | 触摸 h 听气声 |

**TODO（湿实验 9-10 月）**：5 路继电器负载标定 → 写进 `wiki/hardware.md`

## v0.1 协议（8.12 program_v3_1.ino，**已废弃**）

来源：`arduino/program_v3_1.ino` (8.12 写的 Mind+ 转 C 版本，**8.31 已同步到 v0.2**)

| 字符 | 动作 | 引脚 |
|------|------|------|
| `a` | HIGH | PIN 41 |
| `b` | LOW  | PIN 41 |
| `c` | HIGH | PIN 42 |
| `d` | LOW  | PIN 42 |
| `g` | HIGH | PIN 43 |
| `h` | LOW  | PIN 43 |
| `t` | 触发 `DF_fix_data()`，连收 5 字符拼成字符串 | — |

### v0.1 vs v0.2 差异

| 维度 | v0.1 (8.12) | v0.2 (8.31，**当前**）|
|------|------------|------------------|
| 字符数 | 7 (`a-d/g-h/t`) | 9 (`a-i`) |
| 继电器数 | 3 (PIN 41/42/43) | 5 (PIN 41-45) |
| 组合键 | ❌ | ✅ `i` 联动关 44+45 |
| PIN 43 加热膜 | `g`/`h` | `a`/`b` |
| 批量接收 | ✅ `t` 触发 5 字符 | ❌ 移除（DF_fix_data 函数已删除）|

**同步状态（2026-08-31）**：
- ✅ `arduino/program_v3_1.ino` 已重写 `DF_stir_stick_control` 函数（line 149-162）使用 v0.2 协议
- ✅ `arduino/program_v3_1.ino` 已删除 `DF_fix_data` 函数（'t' 批量接收废弃）
- ✅ `arduino/program_v3_1.ino` loop() 已移除 `DF_fix_data()` 调用
- ✅ 头部注释已更新为 v0.2 协议说明

**剩余 TODO（9.1 开学后）**：
- 在 Mind+ 8.31 中正式重新生成 Arduino C 代码（替换当前手写同步的 .ino）
- 5 路继电器物理负载标定（哪个 PIN 接加热膜/蠕动泵/电机/气泵）

## 复现验证

```bash
# 1. 烧程序
arduino-cli upload -p COMx program_v3_1.ino

# 2. 监听串口（USB Serial 0, 115200 baud）
python -c "import serial; s=serial.Serial('COMx', 115200); print(s.readline())"

# 3. 模拟触控屏发送
python -c "import serial; s=serial.Serial('COMx', 9600); s.write(b'a')"  # 开加热膜
python -c "import serial; s=serial.Serial('COMx', 9600); s.write(b'b')"  # 关加热膜
python -c "import serial; s=serial.Serial('COMx', 9600); s.write(b'i')"  # 一键全停（44+45）
```

## 变更历史

- **v0.2 (2026-08-31)** — 老师改版，5 路继电器 + 组合键 `i`，同时同步到 `program_v3_1.ino`
- **v0.1 (2026-08-12)** — 初版，3 路继电器 + 批量接收 `t`（已废弃）
