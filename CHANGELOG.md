# Changelog

All notable changes to the BrewXOS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased] - 2026-08-10 to 2026-09-03

### Added (2026-09-03 v3.2 dual-temp control)
- **PID v3.2 dual-temp firmware** (`arduino/program_v3_2.ino`, 10.3 KB)
  - New **Peltier (PIN 45) auto-control** for overshoot prevention
  - Dead zone 35.3-35.8 °C with hysteresis debounce
  - New `peltier_auto_mode` flag (touchscreen `h` enters manual, `i` returns to auto)
  - Aux heater (PIN 44) stays manual via touchscreen (for strong heating)
  - Heater film PID (PIN 9 PWM) logic **unchanged from v3.1**
  - Backup: `backups/program_v3_1_20260903_pre_v3.2.ino`
- **Python v3.1 vs v3.2 simulator** (`sim_v3_1_vs_v3_2.py`, 9.6 KB)
  - 1st-order RC thermal model (C=200 J/°C, h=0.5 W/°C, T_amb=25 °C)
  - matplotlib dual-plot: temperature comparison + Peltier on/off state
  - 30 min × 2 runs, 1800 steps each
- **2 simulation CSVs** (`data/sim_v3_1_20260903_184734.csv`, `data/sim_v3_2_20260903_184734.csv`)
- **1 comparison PNG** (`data/sim_compare_20260903_184734.png`)

### Changed (2026-09-03)
- **Peltier threshold**: 35.5-36.0 °C → 35.3-35.8 °C (earlier intervention)
- **Peltier power assumption**: 30 W → 80 W (1kW TEC module typical, closer to real hardware)
- **CHANGELOG range**: 8.10-8.13 → 8.10-9.03 (ongoing)

### Simulation Results (v3.1 vs v3.2, 30 min)
| Metric | v3.1 (no Peltier) | v3.2 (Peltier auto) | Improvement |
|--------|-------------------|---------------------|-------------|
| Max overshoot | +1.47 °C | +1.19 °C | **-19%** |
| Settling time | 19s | 19s | same |
| Final error | 0.00 °C | 0.00 °C | same |
| Peltier ON time | — | 1.6 min (98s) | active |

### Pending (lab unavailable 9.3-9.4, push to 9.5 weekend)
- [ ] Hardware flash of program_v3_2 + Serial monitor
- [ ] 35 °C steady-state hardware validation (runbook 9.4 #3)
- [ ] Z-N auto-tune real measurement (runbook 9.3 #3)
- [ ] v3.1 vs v3.2 physical comparison (iGEM wiki Hardware PID Validation section)

---

## [Unreleased] - 2026-08-10 to 2026-08-13

### Added
- **PID v3.1 firmware** with simulation-optimized parameters (Kp=3, Ki=0.05, Kd=3, target=35°C)
- **4 sensor calibration templates** for pH (SEN0161), DO (SEN0237), temperature (DS18B20), CO₂ (SCD4X)
- **DNS reagent protocol** for XOS/xylose quantification (Miller 1959 method + xylose standard curve)
- **Sensor calibration documentation** with 4-sensor wiring diagram (Mega2560)
- **Relay bang-bang control** sketch as hardware fallback (`arduino/relay_test.ino`)
- **PID auto-tuning sketch** using Åström-Hägglund relay feedback method (`arduino/auto_tune.ino`)
- **Coupled ODE fermentation simulator** (6 state variables, RK4 solver, interactive web UI)
- **PID optimization tool** with differential evolution + grid search (`optimize_pid.py`)
- **Serial data logger** for Mind+ format parsing (`serial_24h_logger.py`)
- **Batch launcher** for one-click test runs (`run_24h_test.bat`)
- **System validation report** documenting 8.11-8.13 hardware progress (`wiki/results.md`)

### Changed
- **Target temperature**: 37°C → **35°C** (simulation shows 30-50% higher XOS net accumulation due to reduced Bacillus consumption)
- **PID Kp**: 5.0 → 3.0 (less aggressive, prevents overshoot)
- **PID Kd**: 8.0 → 3.0 (smoother derivative response)
- **PID control loop**: Fixed critical bug where `DF_PID_output()` was defined but never called from `loop()` - now properly invoked every iteration
- **Serial1 baud rate**: 19200 → **9600** (locked by touchscreen hardware requirement)
- **USB Serial baud rate**: 19200 → **115200** (faster debug output)
- **Sensor data format**: removed `.toInt()` casts on n1-n4 outputs, preserving 2-decimal precision

### Fixed
- **Mass conservation bug** in fermentation model: enzymatic xylan hydrolysis now correctly subtracts from substrate pool (`dS/dt = -μ·X/Yxs - Vmax·S/(Km+S)`)
- **Target temperature bug**: original 50°C (set for xylanase optimum, not Bacillus) → 35°C (Bacillus + XOS accumulation optimum)
- **DS18B20 reliability**: original pin 47 sensor dead (read -127°C), replaced with waterproof version with 4.7kΩ pull-up resistor
- **`DF_temp_setting()` scope error**: removed undefined function call from loop (empty function from Mind+ default)
- **pinMode(HEATER_PIN, OUTPUT)**: added explicit setup for reliable PWM output

### Technical Decisions
- **3-year US university plan** (Class of 2033, MIT/Stanford/CMU/Caltech target)
- **Transfer to Star River Bay bilingual school** for AP curriculum in G11-G12 (2027.9 entry)
- **Hardware pivot**: IRF520N MOSFET unavailable for 8.13 → fall back to 5V relay with bang-bang control, MOSFET swap planned for 8.14

### Repository Structure
```
igem2026_shanghai_hongwen_school/
├── arduino/
│   ├── program.ino           # 旧 PID v2 (兼容 Mind+ 触控屏)
│   ├── program_v3_1.ino      # 优化 PID（待 MOSFET 验证）
│   ├── relay_test.ino        # 继电器版（今天用）
│   ├── auto_tune.ino         # 自动调参
│   └── brewXOS_sensor_logger.ino  # 旧版（仅日志）
├── data/
│   ├── cal_pH_20260811.csv
│   ├── cal_DO_20260811.csv
│   ├── cal_temp_20260811.csv
│   └── cal_CO2_20260811.csv
├── docs/
│   └── hardware/
│       ├── DNS_protocol_20260810.md
│       └── sensor_calibration_20260810.md
├── wiki/
│   ├── home.md
│   ├── description.md
│   ├── safety.md
│   ├── team.md
│   ├── attributions.md
│   ├── pre_iGEM_training.md
│   └── results.md            # NEW
├── optimize_pid.py            # PID 优化器
├── test_practical.py          # 实用版测试
├── serial_24h_logger.py       # 串口接收
├── run_24h_test.bat           # 启动器
└── optimization_result.json   # 优化结果
```

---

## Previous Releases

### [v0.1.0] - 2026-07-14 to 2026-08-09
- Initial project setup
- Bacillus subtilis WB800 strain selection
- BSG (brewer's spent grain) substrate validation
- xylanase enzyme screening (Polizeli 2005, Beg 2001, Kulkarni 1999)
- Michaelis-Menten kinetic modeling (3-strain comparison)
- Arduino 4-sensor prototype (Mind+ generated)
- Initial iGEM Wiki structure (home, description, safety, team, attributions)
- Pre-iGEM training: 5-day NMN project (PCR + Gibson + transformation)
- First GitHub push (commits ba890cc, aca7d13, b4f658e, 2f842a7)
