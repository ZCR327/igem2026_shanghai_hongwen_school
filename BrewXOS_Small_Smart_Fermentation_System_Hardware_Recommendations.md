# BrewXOS Small Smart Fermentation System - Hardware Recommendations

**Sub-50 cm Cube Prototype | Brewer's Spent Grain Solid-Liquid Fermentation & Enzymatic Hydrolysis Monitoring | iGEM Hardware Track**

*Author: Thomas ZHAO, Hardware Lead, Shanghai Hongwen School Pudong iGEM 2026 Team*

---

## I. Overall Assessment

**Conclusion:** Build a *desktop-style smart fermentation monitoring system* suitable for iGEM exhibition and small-scale experiments. We do not promise industrial-grade fully automatic sterilization, fully automatic cleaning, or real-time on-line quantification of AXOS structural specificity. Within a 50 cm cube envelope, a more realistic target is a **1-2 L semi-automatic fermentation system** with controllable temperature, agitation, pH / DO / temperature logging, periodic sampling, and colorimetric estimation of reducing-sugar / oligosaccharide release trends - used as a *process-control indicator* for feeding, extending, or terminating the batch.

**Recommended positioning:** **BrewXOS-Fermenter Mini** - a small intelligent solid-liquid fermentation / enzymatic hydrolysis rig. It is *not* an industrial production device. It is a project-validation, education-exhibition, and process-parameter exploration platform.

---

## II. Recommended Prototype Form

| Module | Recommended Design |
|---|---|
| **Footprint** | Whole system within 50 x 50 x 50 cm; suggested base 35 x 35 cm, height 45 cm. |
| **Fermentation vessel** | 1-2 L glass or stainless-steel tank; working volume 0.5-1.2 L; removable sealed lid with pH / DO / temperature / air-in / air-out / sampling ports. |
| **Base controller** | **DFRduino Mega2560 (ATmega2560, 16 MHz, 256 KB Flash, 54 digital I/O, 16 analog in, 4 UARTs)** + I2C LCD / buttons + SD card module / serial data export; optional ESP8266 for Wi-Fi upload. Raspberry Pi option for graphical UI on V3. |
| **Agitation** | Low-cost prototypes use magnetic stirring; switch to top-mounted motor + impeller for viscous BSG slurry (low speed, high torque). |
| **Sensing** | Online: temperature, pH, DO, stirrer RPM. Off-line: automatic / semi-automatic sampling + filtration / centrifugation + colorimetric readout. |
| **Display logic** | Screen shows temperature, pH, DO, fermentation time, colorimetric trend, and *suggested action* prompts ("feed / continue / swap batch"). |

---

## III. Function Feasibility & Implementation Plan

| Function | Feasibility | Implementation Notes & Limits |
|---|---|---|
| **In-place sterilization** | Partially feasible | Industrial-grade SIP needs steam, pressure-rated plumbing, and safety valves - not recommended in a 50 cm cube. Recommended: *removable vessel autoclave + on-line chemical disinfection / hot-water rinse demo*. If autonomous sterilization must be shown, UV-C chamber irradiation, 70% ethanol / H2O2 loop, or hot-water loop are possible - but these are *disinfection / contamination-risk reduction*, **not** full sterilization. |
| **Automatic cleaning** | Demo version feasible | Design a CIP loop: clean water flush -> 0.5-1% NaOH / cleaner loop -> water flush -> 70% ethanol or sanitizer loop -> drain. Use small diaphragm / peristaltic pumps, spray head, and drain valve. Solid BSG residue still needs manual disassembly. |
| **Temperature control** | Easy | Fermentation at 30-45 C via heating film / heating band + DS18B20 / PT100 + PID. For cooling, add a small fan, TEC (Peltier), or water-bath jacket - heating is the priority. |
| **Agitation** | Feasible | Clear / dilute broth: magnetic stirrer. For BSG slurry: top-mounted DC gear motor + impeller, 50-300 rpm variable. Mind the sealing gland and anti-tangle design. |
| **pH monitoring** | Feasible | Lab-grade pH electrode + BNC amplifier module. Calibrate periodically with pH 4.00 / 7.00 buffers. Low-cost pH probes are fine for trend monitoring - not for precision control. |
| **DO monitoring** | Feasible but costly | Electrochemical or optical DO probe. Optical: less maintenance, more expensive. Electrochemical: cheaper, but needs membrane, polarization, and calibration. On a tight budget, use *airflow + stirrer RPM + ORP* as a proxy. |
| **Aeration** | Recommended | For *B. subtilis* aerobic fermentation: small air pump + 0.22 um air filter + check valve + microporous sparger. Also filter the exhaust line. |
| **AXOS off-line detection** | Trend feasible, specificity limited | Colorimetric method (DNS reducing-sugar or other sugar-developing reactions), read absorbance near 540 nm. Reflects reducing-sugar / oligosaccharide release - *cannot* distinguish AXOS degree of polymerization or structure. Final AXOS composition still needs off-line HPLC / HPAEC / TLC / MALDI verification. |
| **Auto-feeding / batch-end decision** | Rule engine feasible | Trigger thresholds from pH, DO, colorimetric slope, fermentation time, and temperature stability. Example: *reducing-sugar growth slows + DO recovers + pH drifts* -> suggest feed or end batch. We recommend **decision prompts**, not fully automated draining. |

---

## IV. AXOS Colorimetric Detection Module Recommendations

Do not claim *"on-line quantification of AXOS"*. A more accurate statement is: *"intermittent colorimetric estimation of reducing-sugar / oligosaccharide release trends, used as a process-control indicator"*. The DNS method is commonly used for reducing-sugar quantification, with absorbance read near 540 nm - but in complex sugar mixtures, the readout is not one-to-one with specific AXOS content.

**Recommended control logic:** Build a D-xylose or XOS standard curve, and use the *rate of change* of colorimetric readings - not absolute AXOS content - to judge the fermentation process. For example, if two consecutive readings grow below threshold and pH / DO indicate metabolism slowing, the system should suggest "consider feeding / extending enzymatic hydrolysis / ending the batch".

---

## V. Suggested Additional Functions

- **Foam detection and anti-foaming prompt:** *B. subtilis* fermentations tend to foam. Use a conductivity probe or photo-electric level sensor to detect foam and trigger anti-foam dosing or reduce aeration.
- **Liquid-level / weight monitoring:** Add a load cell to the base to record mass change from evaporation, feeding, and sampling.
- **Sampling anti-clog design:** BSG is particulate. Sampling ports need a coarse filter, back-flush, or sedimentation chamber. Keep tubing short and detachable.
- **Data logging & visualization:** Write temperature, pH, DO, stirrer RPM, colorimetric readings, and feeding events to SD card or upload to a web dashboard.
- **Safety interlocks:** Over-temperature power cut, low-level pump stop, lid-open agitation stop, leak-tray alarm.
- **Swappable process modes:** Fermentation, enzymatic hydrolysis, cleaning, sanitation, detection.
- **Standard-operating-procedure QR code:** Affix a SOP QR code on the chassis - scan to view loading, calibration, cleaning, waste handling, and safety notes.

---

## VI. Prototype Version Recommendations

| Version | Goal | Main Features | Suitable Scenarios |
|---|---|---|---|
| **V1 - Exhibition prototype** | Build a runnable rig as fast as possible | Temperature control, agitation, pH, temperature, manual sampling + colorimetric, on-screen display | iGEM exhibition, outreach, initial process demo |
| **V2 - Semi-automatic** | Demonstrate hardware innovation | + DO, aeration, peristaltic pump sampling, colorimetric module, data logging, feed-prompt | Project presentation, HP exhibition, lab small-scale trials |
| **V3 - Near-research grade** | Suitable for systematic small trials | + Top-mounted agitation, CIP loop, foam / level sensing, auto-feed decision, web dashboard, detachable sterile ports | Follow-up paper / deeper competition, but cost and debugging time increase significantly |

---

## VII. Cost Estimation (Sub-50 cm Cube Prototype)

The figures below are educational / prototype-level estimates; prices vary with sourcing channel, domestic vs. imported, new vs. used, and required custom fabrication. **DO probes and custom mechanical parts are the most likely budget overruns.**

| Module | Low-end Estimate (RMB) | Recommended Config (RMB) | Notes |
|---|---|---|---|
| Fermentation vessel & frame | 300-800 | 800-2500 | Glass / stainless tank, sealed lid, 3D-printed / acrylic / aluminum frame. |
| Temperature control | 100-300 | 300-800 | Heating film / band, temperature sensor, relay / SSR, insulation; cooling adds cost. |
| Agitation | 150-500 | 500-1500 | Magnetic stirrer is cheap; top-mounted motor + shaft seal + impeller for BSG slurry. |
| pH monitoring | 200-500 | 500-1500 | Low-cost pH module for trends; lab-grade electrode for long-term online use. |
| DO monitoring | 800-1500 | 1500-4000+ | Electrochemical DO probe cheaper; optical DO probe often more expensive. DFRobot DO kit ~USD 169; optical DO solutions reach hundreds of USD. |
| Aeration & filtration | 100-300 | 300-800 | Air pump, 0.22 um air filter, check valve, microporous sparger, flow regulator. |
| Pumps / valves / feed / sampling | 150-500 | 500-1500 | 12 V peristaltic pump, silicone tubing, solenoid valve, waste bottle. |
| Colorimetric detection | 100-400 | 500-1500 | Low-end: phone-based light box. Recommended: 540 nm LED, photodiode, cuvette, heating module. |
| Control & display | 200-600 | 600-1800 | **DFRduino Mega2560 (~RMB 150-250)**, I2C LCD (20x4, ~RMB 60-120), SD card module (~RMB 20-40), buttons, 5V/3.3V PSU; add ESP8266 (~RMB 30-50) for Wi-Fi upload on V2. Raspberry Pi raises cost significantly. |
| Cleaning / sanitation demo | 100-300 | 300-1000 | Cleaning pump, spray head, drain line, UV-C / sanitizer loop; not industrial sterilization. |
| Misc. & fabrication | 300-1000 | 1000-2500 | Fittings, sealing rings, wiring, waterproof enclosure, 3D printing, rework. |

**Overall budget guidance:** V1 (low-end) ~ **RMB 2,500-6,000**; V2 (recommended prototype) ~ **RMB 7,000-15,000**; V3 (research-grade) ~ **RMB 15,000-30,000+**. If a high-quality optical DO probe is selected and significant custom mechanical work is needed, the budget will rise noticeably.

---

## VIII. Recommended Implementation Timeline

- **Week 1:** Finalize vessel, agitation method, and port layout. Sketch piping / wiring diagrams.
- **Week 2-3:** Build temperature control, agitation, pH, temperature display, and data logging. First test with water and simulated media.
- **Week 4:** Add aeration and DO. Complete pH / DO calibration procedure.
- **Week 5:** Build the manual / semi-automatic colorimetric module. Establish xylose / XOS standard curve.
- **Week 6:** Test agitation, anti-clog, and sampling with inactivated BSG suspension. Then move to real small-scale fermentation.
- **Week 7:** Set feed / batch-swap prompt thresholds from data. Build interface and exhibition video.
- **Week 8:** Finalize SOP, cost sheet, risk assessment, hardware iteration log, and Wiki diagrams.

---

## IX. Risks & Statement Boundaries

- Do not call UV / alcohol / hot-water loops "complete sterilization". They should be called "disinfection / contamination-reduction processes". True sterility still requires autoclaving the vessel and media.
- The colorimetric method **cannot** prove that the product is AXOS - it only serves as a process trend. AXOS structure and degree of polymerization still need off-line chromatography / mass spectrometry / thin-layer verification.
- *B. subtilis* fermentation needs careful attention to aerosols, waste-liquid sterilization, and engineered-strain waste handling.
- BSG particulates cause uneven agitation, sampling clogging, and sensor fouling - prioritize mechanical reliability.
- If the prototype is for demonstration, do **not** run it with live engineered strains in an open configuration. Use simulated liquid to demo sensors and control logic.

---

## X. Hardware Highlights for Wiki / Presentation

- Transform BrewXOS's fermentation process from *"black-box cultivation"* into a **visible, logged, and decision-supportable** workflow.
- Use pH, DO, temperature, and colorimetric trends to drive *feed / batch-end decisions* - instead of ending batches blindly on a fixed time schedule.
- Engineer **anti-clog sampling and low-speed high-torque agitation** tailored specifically to the BSG solid-liquid system - a project-specific design.
- Combine *waste valorization + synthetic biology + engineering control* into a single device well-suited for **Education / Human Practices exhibition**.

---

## References

**Pricing references:** DFRobot Arduino pH kit publicly listed at ~USD 29.50; DFRobot analog DO kit publicly listed at ~USD 169; some optical DO sensor vendors quote USD 280-360 class. **Detection reference:** DNS reducing-sugar method is typically read near 540 nm, but in complex sugar mixtures the readout requires a standard curve and careful interpretation.

---

*Document version 1.0 / 2026-08-02 / iGEM 2026 - BrewXOS Team*
