# BrewXOS Metabolic Pathway Model

> **BrewXOS Modeling - v1.0 (2026-09-07)**
> Author: ZHAO Changrui (Thomas)
> Status: 9-state ODE complete, parameter validation pending wet-lab data
> Code: `modeling/brewxos_pathway_v1.py` (~16 KB, scipy.integrate.solve_ivp, LSODA)

This page is the **central iGEM Modeling deliverable** for BrewXOS. It extends
the 6-state coupled ODE (X/S/P/T/pH/DO, described in [Results §2.1](../results.md))
into a **9-state complete metabolic pathway** that captures the full
**BSG → XOS → SCFA** story, including the downstream probiotic function
that is the project's headline.

The page also documents the **cross-disciplinary connection to FTC PID control**,
which is one of the team's strongest T0-application narrative threads.

---

## 1. Why a Pathway Model (not just a Fermenter Model)

iGEM Modeling judging rewards three things:

1. **Comprehensiveness of biological scope** - cover the full pathway, not just one step.
2. **Quantitative parameterization** - every constant has a literature source.
3. **Engineering utility** - the model drives a real design decision.

The previous 6-state ODE (8.13) only covered the fermenter (engineered Bacillus
+ xylan → XOS + T/pH/DO). It missed two things:

- **Xylose as an explicit intermediate** (xylan hydrolysis goes through xylose before transxylosylation produces XOS)
- **Bifidobacterium + SCFA** (the "prebiotic function" half of the project: XOS is not the final product — SCFA produced by gut microbes is)

v1.0 adds these and gets us to a 9-state model that explains the **whole story
the wet lab is trying to tell**.

---

## 2. State Variables (9 states)

| # | State | Symbol | Unit | Initial | Source |
|---|-------|--------|------|---------|--------|
| 0 | Xylan (substrate) | `[Xylan]` | g/L | 10.0 | BSG extract (24h batch) |
| 1 | Xylose (intermediate) | `[Xylose]` | g/L | 0.0 | xylan hydrolysis intermediate |
| 2 | XOS (product) | `[XOS]` | g/L | 0.0 | transxylosylation target |
| 3 | Engineered Bacillus | `X_eng` | g/L | 0.10 | B. subtilis WB800 (xylanase+) |
| 4 | Probiotic Bifido | `X_bifido` | g/L | 0.0 | B. longum (12h post-inoculation) |
| 5 | SCFA | `[SCFA]` | g/L | 0.0 | acetate + propionate + butyrate |
| 6 | Temperature | `T` | °C | 30.0 | PID v3.2 setpoint 37°C |
| 7 | pH | `pH` | - | 7.0 | buffer control to 6.5 |
| 8 | Dissolved oxygen | `DO` | mg/L | 7.0 | aeration control to 4.0 |

---

## 3. Kinetic Equations

### 3.1 Xylan → Xylose (xylanase hydrolysis, Michaelis-Menten + product inhibition)

The engineered *Bacillus subtilis* WB800 secretes xylanase into the broth.
Xylan hydrolysis follows Michaelis-Menten kinetics, **inhibited by accumulated XOS**:

```
v_xylanase = q_xylanase · X_eng · [Xylan] / (Km_xylanase + [Xylan]) · f_T · f_pH / (1 + [XOS] / Ki_XOS)
```

where:

- `q_xylanase = 0.6 g XOS / g X_eng / h` (calibrated to Kulkarni 1999 + Liu 2011 secretion rates)
- `Km_xylanase = 3.2 g/L` (Kulkarni 1999, Bacillus)
- `Ki_XOS = 0.5 g/L` (assumed; wet-lab fit pending)
- `f_T = exp(-((T - T_opt) / T_range)²)` — Arrhenius-like temperature response
- `f_pH = exp(-((pH - pH_opt) / pH_range)²)` — pH response

### 3.2 Xylose → XOS (transxylosylation, first-order)

The transxylosylation step is treated as a first-order reaction (simplified):

```
v_xylosyl = 0.8 · [Xylose] · f_T · f_pH   (h⁻¹, with 95% molar yield to XOS)
```

### 3.3 Engineered Bacillus growth (Monod + logistic cap)

```
μ_eng  = μ_max · [Xylan]/(K_xylan + [Xylan]) · f_T · f_pH
dX_eng = μ_eng · X_eng · (1 - X_eng/X_max) - k_death_eff · X_eng
k_death_eff = k_death · (1 + max(0, T - T_opt) / 5)
```

The `(1 - X_eng/X_max)` logistic cap is critical: without it, the previous
v0 simulation (run 1) showed X_eng runaway to 800 g/L (X_max=5). This is the
key physical correction in v1.0.

### 3.4 Bifidobacterium growth (Monod + logistic, post-12h inoculation)

```
μ_bifido = μ_max · [XOS]/(K_XOS + [XOS]) · f_T · f_pH
dX_bifido = μ_bifido · X_bifido · (1 - X_bifido/X_bifido_max) - k_death_eff · X_bifido + (12h pulse 0.1 g/L)
```

### 3.5 XOS → SCFA (Bifidobacterium catabolism)

```
v_XOS_to_SCFA = (μ_bifido / Y_bifido + μ_max_bifido · 0.05) · X_bifido · f_T · f_pH
dSCFA        = v_XOS_to_SCFA · Y_SCFA
```

`Y_SCFA = 0.42 g SCFA / g XOS` (literature: Bifidobacterium anaerobic fermentation)

### 3.6 Environment (T / pH / DO) — 1st-order with PID

All three follow 1st-order dynamics with PID-style control to setpoints:

- **T**: Q_in (heater 30W when T < T_set - 0.2, off when T > T_set + 0.5) − heat loss (h·(T-T_amb)) + microbial metabolic heat (5·μ·X). C_thermal = 200 J/°C.
- **pH**: SCFA drift (−0.05·[SCFA]) + buffer control (k·(pH_set − pH))
- **DO**: aeration (k_O2_in·(1−DO/8)) − surface off-gas (k_O2_out·DO) − microbial respiration (0.5·μ·X)

This T/pH/DO subsystem uses the same 1st-order RC model as
`sim_v3_1_vs_v3_2.py` (the PID v3.1/v3.2 temperature controller model),
ensuring the pathway model is **dynamically consistent** with the hardware
controller we have already validated in simulation.

---

## 4. Parameters and Literature Sources

| Parameter | Value | Unit | Source | Notes |
|-----------|-------|------|--------|-------|
| `μ_max_eng` | 0.45 | h⁻¹ | Kulkarni 1999 (Bacillus) | Adjustable in `P_eng` |
| `K_xylan` | 0.5 | g/L | This work (assumed) | Wet-lab fit pending |
| `X_max` | 5.0 | g/L | This work | Logistic cap |
| `k_death` | 0.01 | h⁻¹ | This work | Plus temp-dependent enhancement |
| `q_xylanase` | 0.6 | g XOS/g X_eng/h | Calibrated to Kulkarni 1999 + Liu 2011 | **Calibration parameter** |
| `Km_xylanase` | 3.2 | g/L | Kulkarni 1999 | Direct from Bacillus data |
| `Ki_XOS` | 0.5 | g/L | Assumed (literature range 0.2-1.0) | Wet-lab fit pending |
| `T_opt` | 37.0 | °C | Hardware design (`BrewXOS_Small_Smart_Fermentation_System_Hardware_Recommendations.md`) | 30-45°C range |
| `pH_opt` | 6.5 | - | Kulkarni 1999 (Bacillus) | Acidic for fungal alt, neutral for bacterial |
| `T_range` | 8.0 | °C | This work (bell-curve width) | |
| `pH_range` | 1.0 | - | This work | |
| `μ_max_bifido` | 0.30 | h⁻¹ | Literature (Bifidobacterium) | Slow grower |
| `K_XOS` | 0.8 | g/L | This work | |
| `Y_SCFA` | 0.42 | g/g | Literature (Bifidobacterium anaerobic) | |

All parameters live at the top of `brewxos_pathway_v1.py` in the `P_eng`,
`P_bifido`, and `P_env` dicts. Edit them in-place to do sensitivity analysis.

---

## 5. Simulation Results (48h batch, T=37°C, pH=6.5, DO=4.0)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Xylan consumed** | 8.72 g/L (87%) | Substrate near-depletion; reaction complete by ~30h |
| **XOS produced** | 0.24 g/L | Low because consumed by Bifido |
| **SCFA produced** | **3.13 g/L** | ✅ **Headline KPI** — prebiotic function delivered |
| **Xylose residual** | 0.63 g/L | Some intermediate leaks through |
| **B. subtilis (X_eng)** | 4.85 g/L | Hits logistic cap (5.0) |
| **B. longum (X_bifido)** | 1.13 g/L | 36h post-inoculation, still growing |
| **Final T** | 37.1°C | PID stable (overshoot < 0.5°C) |
| **Final pH** | 6.11 | SCFA drift (would need more base dosing) |
| **Final DO** | 6.00 mg/L | Aeration balances microbial respiration |

**Conversion to SCFA yield**: 3.13 g SCFA / 10 g Xylan = **31.3% mass yield** (literature range 25-45% for BSG→SCFA bioprocesses).

### 5.1 PNG Visualization

`brewxos_pathway_v1_<ts>.png` shows 6 panels:
- Top-left: metabolic pathway concentrations (Xylan / Xylose / XOS / SCFA)
- Top-right: microbial growth (B. subtilis + B. longum)
- Middle row: T / pH / DO control
- Bottom-right: yield KPIs over time

The output also writes `brewxos_pathway_v1_<ts>.csv` (481 rows) for downstream
plotly/Flask visualization in the Lab data system.

---

## 6. Sensitivity & Next Steps

| Open question | Plan |
|---------------|------|
| Is `q_xylanase = 0.6` realistic? | Wet-lab xylanase assay: 24h culture supernatant + DNS at 6/12/24/36h |
| Is `Ki_XOS = 0.5` right? | Compare v1.0 prediction to team's batch OD600 + DNS data; refit |
| Does Bifido actually grow on BSG-derived XOS? | Day 7+ wet-lab: 24h XOS-supplemented B. longum culture |
| Can SCFA hit 5 g/L? | v1.1: optimize inoculation timing + pH control + aeration strategy |

The v1.0 framework is the **scaffold**. v1.1 will be the **fitted model** once
wet-lab OD600 + DNS + HPLC data arrives.

---

## 7. Cross-Disciplinary Bridge: From FTC PID to Metabolic Modeling

The pathway model is **not just biology**. It uses the same control-theoretic
primitives I have already deployed in FTC robotics:

| BrewXOS modeling | FTC robotics (Team 24068 / 19606) |
|------------------|-------------------------------------|
| PID temperature controller (v3.1/v3.2) | PID drivetrain controller (FTC SDK) |
| 1st-order RC thermal model (this page) | 1st-order DC motor model (FTC libs) |
| `solve_ivp` LSODA integration | `DifferentialDrive` kinematics integration |
| Arrhenius-like temperature compensation | Battery voltage compensation in trajectory planner |
| Logistic growth cap = physical safety | Slew rate limit = software safety |

The same engineering language — **state, ODE, PID, calibration, validation** —
shows up in both. The pathway model is a **deliberate reuse** of the team's
FTC systems-engineering toolkit on a synthetic-biology problem.

This is the headline story for T0 applications: an engineer who can move
between **robotics** (FTC) and **bioprocess control** (iGEM) using the same
mental models.

---

## 8. Reproducibility

- **Code**: `modeling/brewxos_pathway_v1.py` (Python 3.11, scipy 1.15, numpy 2.2, matplotlib 3.10, pandas 2.x)
- **Run time**: ~3 seconds for 48h horizon
- **Inputs**: edit `P_eng`, `P_bifido`, `P_env`, `IC`, `T_HORIZON` at the top of the file
- **Outputs**:
  - `brewxos_pathway_v1_<ts>.csv` (481 rows, full time series)
  - `brewxos_pathway_v1_<ts>.png` (6-panel visualization, 120 dpi)
  - `brewxos_pathway_v1_<ts>_metrics.json` (final-state summary + parameters)
- **Verification**: First run (without logistic cap) showed X_eng runaway to 800 g/L, confirming the cap is necessary. With the cap, results are physically bounded.

---

## 9. Future Work (Roadmap)

- **v1.1** (after wet-lab data): replace `q_xylanase` / `Ki_XOS` with fitted values via `scipy.optimize.curve_fit`
- **v1.2**: add BSG pretreatment ODE (alkaline extraction + temperature) — upstream of this model
- **v2.0**: add Flux Balance Analysis (FBA) on a genome-scale model of *B. subtilis* WB800 to predict optimal xylanase secretion pathways
- **v2.1**: stochastic version (Langevin noise on μ_max to capture batch-to-batch variability)
- **v3.0**: closed-loop control via Lab data system — auto-update parameters from streaming OD600 / DNS measurements

---

## 10. References

1. Kulkarni, N., Shendye, A., & Rao, M. (1999). Molecular and biotechnological aspects of xylanases. *FEMS Microbiol Rev*, 23(4), 411-456.
2. Beg, Q. K., Kapoor, M., Mahajan, L., & Hoondal, G. S. (2001). Microbial xylanases and their industrial applications. *Appl Microbiol Biotechnol*, 56(3-4), 326-338.
3. Polizeli, M. L. T. M., et al. (2005). Xylanases from fungi: properties and industrial applications. *Appl Microbiol Biotechnol*, 67(5), 577-591.
4. Liu, M. Q., et al. (2011). Hyper-secreting *Bacillus subtilis* xylanase strain. *Biotechnol Bioeng*, 108(12), 2841-2851.
5. Roberfroid, M. B. (2007). Prebiotics: the concept revisited. *J Nutr*, 137(3), 830S-837S. (XOS → SCFA prebiotic function)
6. Simpson, P. J., et al. (2003). *Bifidobacterium* growth on XOS. *Appl Environ Microbiol*.
7. Hardware: `docs/hardware/serial_protocol_20260831.md` (PID v3.2 controller, 1024×600 TFT)
8. Predecessor: `wiki/design/modeling_comparison.md` (Day 2, strain selection)
9. Predecessor: `wiki/results.md` §2.1 (6-state coupled ODE, 8.13)
