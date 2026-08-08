# Xylanase Strain Modeling Comparison

> **BrewXOS Modeling - Day 2 result**  
> Date: 2026-08-05  
> Status: Preliminary (literature-based, team wet-lab data pending)

This page compares **3 candidate xylanase-producing strains** in the literature for their fit with the BrewXOS fermentation system. The model is implemented in `day2_enzyme_hydrolysis.py` (see GitHub).

---

## 1. Strain Sources

| Strain code | Organism | Source | Why we picked it |
|-------------|---------|--------|------------------|
| **Polizeli_2005_Aspergillus** | *Aspergillus* sp. (fungus) | Polizeli et al. 2005, *Appl Microbiol Biotechnol* 67: 577-591 | Industry workhorse for fungal xylanases |
| **Beg_2001_Trichoderma** | *Trichoderma* sp. (fungus) | Beg et al. 2001, *Appl Microbiol Biotechnol* 56: 326-338 | High Vmax reported; widely studied |
| **Kulkarni_1999_Bacillus** | *Bacillus* sp. (bacterium) | Kulkarni et al. 1999, *FEMS Microbiol Rev* 23: 411-456 | Closest to our proposed chassis (*B. subtilis*) |

## 2. Core Kinetic Parameters (from literature)

| Parameter | Polizeli (Aspergillus) | Beg (Trichoderma) | Kulkarni (Bacillus) | Unit |
|-----------|------------------------|-------------------|---------------------|------|
| K_m (xylan) | 2.5 | 1.8 | 3.2 | mg/mL |
| V_max | 28.0 | 35.0 | 22.0 | U/mg |
| T_opt (operating) | 45 | 50 | 37 | C |
| pH_opt | 5.5 | 5.0 | 6.5 | - |
| Product inhibition K_i | 0.5 | 0.5 | 0.5 | mg/mL (assumed) |
| Conversion to XOS | 95 | 95 | 95 | % (assumed) |

## 3. 24-hour Batch Simulation (T = 40 C, S0 = 10 mg/mL, E = 0.5 mg/mL)

| Metric | Polizeli (Aspergillus) | Beg (Trichoderma) | Kulkarni (Bacillus) | Winner |
|--------|------------------------|-------------------|---------------------|--------|
| **XOS at 6 h** (mg/mL) | 1.82 | 2.13 | 1.34 | Beg |
| **XOS at 12 h** (mg/mL) | 3.21 | 3.74 | 2.41 | Beg |
| **XOS at 24 h** (mg/mL) | 5.12 | 5.78 | 3.98 | Beg |
| **Residual xylan at 24 h** (mg/mL) | 4.21 | 3.55 | 5.47 | Beg |
| **Conversion at 24 h** | 51% | 58% | 40% | Beg |
| **Max instantaneous rate (U/mg) at 6 h** | 8.4 | 10.1 | 6.2 | Beg |

## 4. Temperature Sensitivity (24-h XOS yield, Vmax scaled by Arrhenius)

| Temperature (C) | Polizeli | Beg | Kulkarni | Notes |
|------------------|----------|-----|----------|-------|
| 25 | 2.10 | 1.85 | 3.45 | Bacillus wins below 30 C |
| 30 | 3.50 | 3.10 | 3.95 | Bacillus still ahead |
| 35 | 4.60 | 4.20 | 4.10 | Cross-over zone |
| **40** | **5.12** | **5.78** | 3.98 | **Fungal strains peak (40-45 C)** |
| 45 | 5.20 | 6.45 | 2.85 | Beg hits its peak |
| 50 | 4.50 | 6.10 | 1.20 | Beg still strong at 50 C |
| 55 | 3.10 | 4.85 | 0.20 | Beg only strain that survives |

## 5. Engineering Trade-off Summary

| Criterion | Polizeli | Beg | Kulkarni |
|-----------|----------|-----|----------|
| **Maximum yield (24 h)** | Medium (5.1 mg/mL) | **Best (5.8 mg/mL)** | Low (4.0 mg/mL) |
| **Speed to peak** | Medium | Fastest | Slowest |
| **Temperature flexibility** | Good (35-50 C) | Excellent (30-55 C) | Narrow (30-40 C) |
| **pH tolerance** | Acidic (5.0-6.0) | Acidic (4.5-5.5) | Neutral (6.0-7.0) |
| **Chassis compatibility with *B. subtilis* WB800** | Low (fungus) | Low (fungus) | **High (same genus!)** |
| **Lab cultivation difficulty** | Medium | Medium | **Easy** |
| **Process cost (USP)** | High | High | **Low** |
| **Genetic tools availability** | Limited (eukaryotic) | Limited (eukaryotic) | **Excellent (prokaryotic)** |

## 6. Recommended Strain for BrewXOS

> **Primary recommendation: *Bacillus subtilis* chassis (Kulkarni 1999 framework + our own tuning)**

### Why Bacillus, even though Beg has higher peak yield:

1. **Single-cell process** - we want a *B. subtilis* that **secretes its own xylanase into the same bioreactor** that produces XOS. *B. subtilis* is naturally protein-secreting (industrial workhorse for amylase, protease, etc.). Fungal strains would require a separate fermentation step.
2. **37 C operating temperature** - matches our hardware design (30-45 C is the recommended range in `BrewXOS_Small_Smart_Fermentation_System_Hardware_Recommendations.md`). Fungal strains need 45-50 C, requiring extra heating.
3. **pH 6.5** - closer to the slightly acidic range that *B. subtilis* tolerates natively; avoids the pH-control burden of fungal strains (pH 5.0-5.5 means more acid/base dosing).
4. **Prokaryotic chassis** - much simpler genetic tools, faster iteration, lower cost.
5. **Path to V3** - if we want to engineer further (e.g., surface display, fusion tags, secretion optimization), the *B. subtilis* toolkit is the deepest in synthetic biology.

### Why we keep the fungal comparison:

- If the **wet-lab team discovers** that *B. subtilis* secretion is too low, we have a documented fallback path: use a fungal xylanase in a **two-step process** (separate fermentation + hydrolysis).
- The modeling result (**Beg's 5.8 mg/mL vs Bacillus's 4.0 mg/mL at 24 h**) gives the **upper bound** on what we can achieve with a perfect enzyme. This sets the **target for strain engineering**.

## 7. Sensitivity & Uncertainty

The model currently has the following uncertainty sources:

| Parameter | Literature range | Impact on XOS prediction |
|-----------|-----------------|--------------------------|
| K_m | +/- 0.5 mg/mL | +/- 8% XOS |
| V_max | +/- 5 U/mg | +/- 15% XOS |
| Product inhibition K_i | 0.2 - 1.0 mg/mL | +/- 12% XOS |
| Temperature Arrhenius Ea | 35-50 kJ/mol | +/- 10% XOS |

**Action**: our team's own wet-lab data will replace these placeholders. The `fit_team_data()` function in `day2_enzyme_hydrolysis.py` is already wired up for that.

## 8. Connection to Other BrewXOS Components

| Component | How this model connects |
|-----------|------------------------|
| **Hardware** (V2 enclosure) | Recommends 37 C operating temperature; informs heating membrane sizing |
| **Lab data system** (Flask + SQLite) | Will store wet-lab OD600 + XOS measurements, then call `fit_team_data()` |
| **iGEM Wiki** (modeling.md) | This comparison table is the centerpiece of the Wiki modeling page |
| **FTC PID control** | Same Arrhenius-like temperature compensation logic applies to both robots and bioreactors |

## 9. Next Steps

- [ ] **Day 3**: Add BSG pretreatment ODE (alkaline extraction + temperature) - upstream of this model
- [ ] **Day 4**: Add product inhibition scan + substrate concentration sweep
- [ ] **Day 5**: Connect to Lab data system - auto-fit when team data arrives
- [ ] **Day 6**: Write `wiki/design/modeling.md` page using this table
- [ ] **Day 7+**: Wet-lab strain characterization (B. subtilis xylanase secretion assay)

## 10. Reproducibility

- **Code**: `day2_enzyme_hydrolysis.py` (Python 3.11, scipy 1.11, numpy 1.26, matplotlib 3.8)
- **Run time**: ~3 seconds
- **Inputs**: edit `LITERATURE_PARAMS` or `TEAM_PARAMS` to change strain parameters
- **Outputs**: `day2_literature_comparison.png`, `day2_temperature_sensitivity.png`

## 11. References

1. Polizeli, M. L. T. M., et al. (2005). *Appl Microbiol Biotechnol* 67: 577-591.
2. Beg, Q. K., et al. (2001). *Appl Microbiol Biotechnol* 56: 326-338.
3. Kulkarni, N., et al. (1999). *FEMS Microbiol Rev* 23: 411-456.
4. Liu, M. Q., et al. (2011). *Biotechnol Bioeng* 108(12): 2841-2851. (B. subtilis xylanase hyper-secreting strain)
