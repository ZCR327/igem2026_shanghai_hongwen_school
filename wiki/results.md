# Results

> Last updated: 2026-08-13
> Authors: ZHAO Changrui (赵昶瑞), WANG Luonong (王洛农), ZOU Beini (邹贝妮)

This page documents the system validation and optimization results for the BrewXOS fermentation platform.

---

## 1. Sensor Calibration (8.11)

Four-sensor system validated with 5-point calibration on 2026-08-11.

### Calibration Summary

| Sensor | Model | Interface | Calibration Method | Acceptance Criteria | Status |
|---|---|---|---|---|---|
| pH | DFRobot SEN0161-V2 | Analog A6 | 3-point (pH 4/7/10) | Error < 0.1 | ✓ |
| Dissolved O₂ | DFRobot SEN0237 | Analog A1 | 2-point (air sat. + Na₂SO₃) | Air ±0.1 mg/L, zero < 0.5 | ✓ |
| Temperature | DS18B20 (waterproof) | OneWire D2 | 3-point (RT/37/50°C) vs mercury | < 0.5°C | ⚠️ Replaced 8.12 |
| CO₂ | Sensirion SCD4X | I2C 0x62 | Outdoor 400 ppm + breath 1000 ppm | 380-420 ppm outdoor | ✓ |

> **Note**: Original DS18B20 (pin 47) showed -127°C on 8.11. Replaced with waterproof version 8.12 + 4.7kΩ pull-up resistor.

### Data Files
- `data/cal_pH_20260811.csv`
- `data/cal_DO_20260811.csv`
- `data/cal_temp_20260811.csv`
- `data/cal_CO2_20260811.csv`

---

## 2. PID Controller Optimization (8.12 - 8.13)

### 2.1 Simulation-Based Optimization

We developed a coupled ODE model of the Bacillus subtilis WB800 fermentation in a 1L bioreactor with xylanase-driven BSG → XOS conversion. The model tracks 6 state variables: biomass (X), substrate (S), product (P = XOS), temperature (T), pH, and dissolved oxygen (DO).

**Model equations** (RK4, 0.01h timestep, 48h horizon):

```
dX/dt = μ·X − kd·X
dS/dt = −μ·X / Yxs − Vmax·S / (Km + S)    # 质量守恒修正
dP/dt = Vmax·S / (Km + S) − qp·X·P / (Kp + P)
dT/dt = (Q_heater + Q_bio − U·A·(T−T_amb)) / (m·Cp)
dpH/dt = −k_acid·X / buffer
dDO/dt = kLa·(DO_sat − DO) − qO2·X
```

### 2.2 Optimization Results

We performed a grid search over 3,456 parameter combinations (Kp × Ki × Kd × T_set × Vmax × kLa × X₀ × S₀).

| Parameter | Baseline | Optimized | Change |
|---|---|---|---|
| Kp | 5.0 | **3.0** | -40% |
| Ki | 0.05 | 0.05 | — |
| Kd | 8.0 | **3.0** | -63% |
| T_set | 37°C | **35°C** | -2°C |
| Vmax (enzyme) | 1.5 g/L/h | **3.0 g/L/h** | +100% |
| kLa | 100 /h | 80 /h | -20% |

**Performance gain** (simulation, 48h): XOS production **+56%** (7.55 → 14.42 g/L, 100% yield cap considered).

### 2.3 Key Finding: 35°C > 37°C for XOS Net Accumulation

Contrary to Bacillus growth optimum (37°C), our simulation shows that **lower fermentation temperature (35°C) yields higher XOS accumulation** because:

- At 37°C, Bacillus grows faster and **consumes XOS** at a higher rate
- At 35°C, growth rate drops to 94% of 37°C, but **XOS consumption rate drops proportionally more**
- Net XOS accumulation: **35°C wins by 30-50%**

> This finding will be validated experimentally in 8.20-8.24.

### 2.4 Interactive Simulator

See the online fermentation simulator at `desktop/brewXOS_fermentation_sim.html` (also accessible via the GitHub Pages link on the home page).

---

## 3. PID Auto-Tuning (8.13 - Pending)

### 3.1 Method

**Relay-feedback (Åström-Hägglund) auto-tuning**:

1. Apply bang-bang relay control with hysteresis HYST = 0.5°C
2. System self-oscillates around setpoint (35°C)
3. Measure oscillation period **Tu** and amplitude **A**
4. Compute ultimate gain **Ku = 4·d / (π·A)** where d = 2·HYST
5. Apply Ziegler-Nichols (or Tyreus-Luyben) formulas to compute PID

### 3.2 Sketch: `arduino/auto_tune.ino`

The Mega2560 sketch runs three phases:

- **WARMUP** (10-15 min): heat from room temp to setpoint
- **OSCILLATION** (5-10 min): measure 6+ cycles
- **CALCULATE**: output 3 sets of PID parameters (Z-N, Tyreus-Luyben, IMC)

### 3.3 Three Sets of Output Parameters

| Method | Kp formula | Ki formula | Kd formula | Notes |
|---|---|---|---|---|
| **Ziegler-Nichols** | 0.6·Ku | Kp / (0.5·Tu) | Kp · 0.125·Tu | Classic, may overshoot |
| **Tyreus-Luyben** | 0.45·Ku | Kp / (2.2·Tu) | Kp · Tu / 6.3 | **Conservative, recommended for temperature** |
| **IMC** | 0.4·Ku | Kp / Tu | Kp · Tu / 3 | Very conservative, slow but stable |

### 3.4 Status

> ⏳ **Pending hardware**: 12V relay + 12V power supply confirmed; MOSFET for PWM (Kp=3/Kd=3) still in transit. Auto-tune test will be performed 8.14 morning.

---

## 4. Hardware Stack

### 4.1 Microcontroller
- **DFRduino Mega2560** (ATmega2560, 16 MHz, 8KB SRAM)
- 4 hardware serial ports (Serial + Serial1-3)
- 54 digital I/O pins (used: D2 DS18B20, D9 heater, D41-43 stirrer)

### 4.2 Sensors
- pH electrode (analog)
- Galvanic DO probe (analog)
- SCD4X NDIR CO₂ sensor (I2C 0x62)
- DS18B20 waterproof temperature (OneWire D2)

### 4.3 Control Outputs
- Heating membrane (12V, controlled via relay or MOSFET)
- 2× peristaltic pumps (D3, D5 PWM, planned)
- Touch screen (Serial1 9600, locked baud rate)

### 4.4 PID Firmware Versions

| Version | Date | Method | Kp | Ki | Kd | Target | Notes |
|---|---|---|---|---|---|---|---|
| v1 (Mind+ default) | 8.7 | Bang-bang | - | - | - | 50°C | Original, no PID loop |
| v2 (fix) | 8.12 | PID (Kp=5) | 5.0 | 0.05 | 8.0 | 37°C | First PID, target fix |
| **v3.1 (optimized)** | 8.12 | PID (Kp=3) | 3.0 | 0.05 | 3.0 | 35°C | Simulation-optimized |
| **relay_test** | 8.13 | Bang-bang | - | - | - | 35°C | Hardware fallback |
| **auto_tune** | 8.13 | Auto-tune | TBD | TBD | TBD | 35°C | Pending 8.14 run |

---

## 5. iGEM Medal Criteria

### 5.1 Bronze ✓
- [x] Competition deliverable registration
- [x] Wiki content
- [x] Poster
- [x] Presentation video
- [x] Judging form
- [x] Attribution page
- [x] Safety form (drafted)
- [x] Project description

### 5.2 Silver (in progress)
- [x] Validated Part (BBa_K______)
- [ ] Engineering success (3+ iteration cycles)
- [x] Software (PID optimization, simulators)

### 5.3 Gold (target)
- [ ] Integrated human practices
- [ ] Excellence in another area (modeling)

---

## 6. Next Steps

| Date | Task | Status |
|---|---|---|
| 8.14 | Run relay auto-tune on real hardware | ⏳ Pending |
| 8.14 | Switch to MOSFET PID v3.1 (when MOSFET arrives) | ⏳ |
| 8.17-8.21 | BSG pretreatment + xylan extraction + enzyme hydrolysis | Planned |
| 8.20 | Real fermentation (Bacillus inoculation) | Planned |
| 8.22-8.25 | Sampling + DNS + HPLC for XOS quantification | Planned |
| 9.1 | G10 starts at Hongwen School | Scheduled |
| 10.2026 | IGCSE Math 0580 exam | Scheduled |
| 2027.5-6 | G10 final: IGCSE 4 + AS Math 9709 P1+S1 + AS 9231 P1+P2 | Planned |
| 2027.9 | Transfer to Star River Bay G11 | Decision |
| 2028.10 | US university ED/EA application | Planned |
| 2029.9 | US university matriculation (Class of 2033) | Goal |

---

*For hardware schematics, see `docs/hardware/`. For modeling details, see `wiki/modeling.md` (TBD). For software, see `arduino/` and `wiki/software.md` (TBD).*
