# Hardware Design

> **Status**: Version 2 (B) deployed for iGEM 2026 Wiki freeze.  
> **Lead designer**: Thomas ZHAO (赵昶瑞), Shanghai Hongwen School Pudong.  
> **Tool chain**: Autodesk Fusion 360 -> STEP AP214 export.

---

## 1. Why this matters

The BrewXOS fermentation system turns brewer's spent grain (BSG) into xylo-oligosaccharides (XOS) for gut-health prebiotics. To make this **visible, logged, and decision-supportable** (instead of "black-box cultivation"), the team designed a custom hardware enclosure around a small (1-2 L) semi-automatic fermentation rig with continuous multi-parameter sensing.

This page documents the **two-stage design iteration** that took the rig from a working bench-top prototype (V1) to a sealed, modular, product-grade enclosure (V2) in 16 hours.

---

## 2. Design Goals

| # | Goal | Engineering question |
|---|------|---------------------|
| G1 | Compact 50 x 50 x 50 cm footprint | "Can we fit the whole rig under one desk?" |
| G2 | Six-parameter real-time display | "Can an operator read the system state in one glance?" |
| G3 | Modular separation of wet zone and dry zone | "Can we service electronics without opening the bioreactor?" |
| G4 | Sealed, SIP-ready enclosure | "Can we run industrial-grade sterilization-in-place?" |
| G5 | Multi-interface extensibility (pH / DO / T / sampling / feed) | "Can we add more sensors without redesigning?" |

V1 addressed **G1 and G2**; V2 addressed **G3, G4, and G5**.

---

## 3. Version 1 (2026-08-03, 242 KB STEP)

### Design philosophy
> "Make it work" - prioritize internal functionality and rapid validation.

### What V1 delivered
- Glass fermentation vessel (transparent for direct observation)
- 6-parameter LCD display: CO2 evolution rate, O2 concentration, pH accuracy, cumulative range, H2/air, temperature
- Single top-mounted sensor / agitator rod
- Flat base
- Basic L-shaped overall structure

### What V1 lacked
1. Open top -> not suitable for industrial-grade SIP / hygiene
2. Exposed vessel -> reads as bench-top lab equipment, not a product
3. Single interface -> poor extensibility
4. Flat base -> center of gravity and vibration unoptimized
5. No modular separation -> vessel, control, and display mixed

![V1 Top View](../static/images/hardware/shell_v1_top.png)
![V1 Front View](../static/images/hardware/shell_v1_front.png)
![V1 Left View](../static/images/hardware/shell_v1_left.png)

*Figure 1. Version 1 - top, front, and left views. Note the open top and exposed vessel.*

---

## 4. Version 2 (2026-08-04, 458 KB STEP, +89% detail density)

### Design philosophy
> "Package the internals into a deliverable" - product-grade appearance, manufacturability, serviceability.

### Five concrete improvements

| # | Improvement | Engineering rationale |
|---|------------|----------------------|
| 1 | **Full sealed enclosure** with top cover | SIP-ready; meets hygiene requirements |
| 2 | **Vessel cladding** - lower half integrated into shell | Industrial aesthetic; mechanical protection |
| 3 | **Beveled base** | Improved center of gravity; vibration damping; modern look |
| 4 | **Left-side L-extension** | Multi-interface layout: sampling / pH / DO / feed |
| 5 | **Modular zoning** - circular fermentation zone + rectangular control zone, **physically separated** | Fault isolation; easy maintenance; future upgrade path (V3 WiFi / automation) |

### What V2 preserved from V1
- 6-parameter LCD display (unchanged)
- Glass vessel (still visible for process observation)
- Overall L-shape (backward-compatible footprint)

![V2 Side View](../static/images/hardware/shell_v2_side.png)
![V2 Top View](../static/images/hardware/shell_v2_top.png)
![V2 Section View](../static/images/hardware/shell_v2_section.png)

*Figure 2. Version 2 - side, top, and section views. Note the sealed top, modular zoning, and beveled base.*

---

## 5. Design Principles (carried forward)

1. **Function first, then productization** - V1 made the system work; V2 made it shippable.
2. **Modularization** - fermentation zone (vessel + sensors + heater + agitator) and control zone (DFRduino Mega2560 + LCD + interfaces) are physically separate modules.
3. **Data-driven decisions** - every V2 change is grounded in a concrete V1 use issue.
4. **Cross-disciplinary integration** - mechanical (Fusion 360) + control (DFRduino Mega2560) + sensor interface (pH / DO / T / sampling / feed) + industrial design (UX / hygiene).

---

## 6. Sensor and Interface Mapping (V2)

| Position | Sensor / Interface | Purpose |
|----------|-------------------|---------|
| Top cover | pH electrode port (BNC) | Real-time pH monitoring |
| Top cover | DO probe port (PG13.5) | Dissolved oxygen monitoring |
| Top cover | PT100 / DS18B20 | Temperature (PID control) |
| Top cover | Sampling port with anti-clog filter | Manual or auto sampling |
| Left L-extension | Peristaltic pump inlet | Feed / base addition |
| Left L-extension | Air inlet + 0.22 um filter | Aeration for B. subtilis |
| Left L-extension | Air outlet + condenser | Exhaust + vapor recovery |
| Front panel | 6-parameter LCD | Real-time operator display |
| Front panel | Push buttons (4) | Mode / confirm / up / down |
| Bottom | Drain valve | Batch drain |
| Bottom | Level sensor (load cell) | Mass-based process tracking |

---

## 7. Controller Architecture

**Main controller**: DFRduino Mega2560 (ATmega2560, 16 MHz, 256 KB Flash, 54 digital I/O, 16 analog in, 4 UARTs).

Why DFRduino Mega2560:
- 54 I/O pins (BrewXOS uses ~15, plenty of headroom)
- 4 UARTs (pH + DO + WiFi expansion + debug)
- 5V-compatible with the DFRobot sensor ecosystem (pH kit, DO kit, weight sensor)
- Industrial-grade DFRobot customization (better power filtering than the bare Mega)
- Direct Arduino IDE compatibility (zero learning cost for the team)

**Future V3 controller expansion** (planned):
- ESP8266 for Wi-Fi data upload to a web dashboard
- Optional Raspberry Pi for full graphical UI

---

## 8. Cost Estimation (V2, 50 cm cube prototype)

| Module | Low-end (RMB) | Recommended (RMB) | Notes |
|--------|---------------|-------------------|-------|
| Fermentation vessel & frame | 300-800 | 800-2500 | Glass / stainless tank, sealed lid, 3D-printed / acrylic / aluminum frame |
| Temperature control | 100-300 | 300-800 | Heating film / band, PT100 / DS18B20, SSR, insulation |
| Agitation | 150-500 | 500-1500 | Magnetic stirrer (cheap) or top DC gear motor + impeller (for BSG slurry) |
| pH monitoring | 200-500 | 500-1500 | DFRobot pH kit (USD ~29.50 list) for trend; lab electrode for long-term |
| DO monitoring | 800-1500 | 1500-4000+ | DFRobot analog DO kit (USD ~169 list); optical probe 2-3x more |
| Aeration & filtration | 100-300 | 300-800 | Air pump, 0.22 um filter, check valve, microporous sparger |
| Pumps / valves / feed / sampling | 150-500 | 500-1500 | 12 V peristaltic pump, silicone tubing, solenoid valve, waste bottle |
| Colorimetric detection | 100-400 | 500-1500 | 540 nm LED, photodiode, cuvette, heating module (DNS method) |
| Control & display | 200-600 | 600-1800 | DFRduino Mega2560 (~RMB 150-250), I2C LCD, SD card, ESP8266, PSU |
| Cleaning / sanitation demo | 100-300 | 300-1000 | Cleaning pump, spray head, drain line, UV-C / sanitizer loop |
| Misc. & fabrication | 300-1000 | 1000-2500 | Fittings, sealing rings, wiring, waterproof enclosure, 3D printing |
| **Total V2 (recommended)** | | **~7000-15000** | |

---

## 9. V3 Roadmap (post-September 2026)

- Integrate top-mounted agitator motor (reusing the V1 single-rod location)
- Reserve DO sensor port (PG13.5 fitting)
- Integrate CIP (clean-in-place) piping
- Web dashboard (data upload via ESP8266 -> Flask + ECharts visualization)
- Add a top-mounted foam sensor (conductivity probe)
- Modular, detachable electronics panel for easier field service

---

## 10. Why two-stage iteration matters for iGEM

iGEM judges look for **engineering iteration under real constraints**, not a one-shot pretty render. Our V1 -> V2 story shows three things:

1. **Rapid learning cycle** - 16-hour turnaround from a working V1 to a sealed, modular V2
2. **Cross-functional decision-making** - the V2 redesign considered SIP hygiene, modularity, serviceability, and product aesthetics simultaneously
3. **Process discipline** - every V2 change is justified by a concrete V1 problem, not by aesthetics alone

The same iteration discipline drives the team's modeling work: each metabolic model is a "V1" that gets refined into a "V2" once experimental data is available.

---

## 11. Downloads

- **V1 STEP file**: [igem.step](../../igem.step) (242 KB, STEP AP214)
- **V2 STEP file**: [B_Step.zip](../../整体外壳B.STEP) (458 KB, STEP AP214)
- **CAD screenshots**: see `static/images/hardware/`

## 12. Authorship

- **Hardware design & lead**: Thomas ZHAO (赵昶瑞), Shanghai Hongwen School Pudong
- **Controller & sensors**: DFRduino Mega2560 platform with DFRobot pH / DO kits
- **Project**: BrewXOS - iGEM 2026 - Shanghai Hongwen School Pudong
