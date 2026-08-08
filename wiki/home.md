# BrewXOS

**Turning millions of tons of brewery waste into gut-health prebiotics.**

---

## Project Summary

BrewXOS is an iGEM 2026 project by the Shanghai Hongwen School Pudong team. We engineer a biological system to convert **brewer's spent grain (BSG)** - one of the world's largest food-industry waste streams (~39 million tons per year globally) - into **xylo-oligosaccharides (XOS)**, a high-value prebiotic that supports human gut health.

---

## The Three Pillars

| Pillar | What we do | Why it matters |
|--------|-----------|----------------|
| **Synthetic biology** | Engineer *B. subtilis* to produce xylanase and secrete XOS from BSG-derived xylan | Sustainable production of a high-value prebiotic from waste |
| **Hardware** | Custom 1-2 L bioreactor with 6-parameter real-time sensing (CO2 / O2 / pH / cumulative / H2 / temperature) | Replace "black-box cultivation" with visible, logged, decision-supportable fermentation |
| **Modeling** | ODE-based Michaelis-Menten kinetics, FBA flux analysis, and dynamic fermentation simulation | Predict gene-knockout effects and optimize xylanase productivity *in silico* before wet-lab validation |

---

## Project Roadmap

```
2026.08 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2026.11
  │
  ├─ ● Aug 1-7:   Hardware V1 -> V2 ✅ | Wiki scaffold ✅
  ├─ ○ Aug 8-15:  Modeling Day 2-7 (COBRApy + ODE)
  ├─ ○ Aug 16-31: Wet-lab strain construction
  ├─ ○ Sep 1-15:  Fermentation trials + data fitting
  ├─ ○ Sep 16-30: Hardware V3 (DO sensor + WiFi)
  ├─ ○ Oct 1-31: Wiki final freeze (Oct 28 typical)
  └─ ● Nov 1-15:  iGEM Grand Jamboree (Paris or remote)
```

Legend: `●` done  `○` planned

---

## Recent Updates

| Date | Update |
|------|--------|
| 2026-08-04 | **Hardware shell V2** released - sealed enclosure with modular fermentation + control zones (458 KB STEP) |
| 2026-08-03 | **Hardware shell V1** released - functional prototype with 6-parameter LCD (242 KB STEP) |
| 2026-08-02 | **Wiki structure** scaffolded (Flask + Markdown); **modeling pipeline** (COBRApy) initialized |

---

## Project Status (Live Indicators)

- [x] **Hardware V1** complete and tested
- [x] **Hardware V2** complete (16-hour iteration)
- [x] **Wiki scaffold** running on Flask
- [x] **Modeling** baseline (iJO1366 FBA) tested
- [ ] **Strain construction** in progress
- [ ] **Fermentation wet-lab** starting
- [ ] **V3 hardware** (DO sensor + web dashboard) planned

---

## Quick Facts

- **Project name**: BrewXOS
- **Team**: Shanghai Hongwen School Pudong (上海宏文学校浦东校区)
- **Year**: 2026
- **Track**: Hardware + Software + Modeling
- **Substrate**: Brewer's spent grain (BSG)
- **Product**: Xylo-oligosaccharides (XOS) - gut-health prebiotic
- **Host organism**: *Bacillus subtilis* (proposed)
- **Open source**: All code, CAD, and documentation on GitHub

---

## Navigation

- [Description](description) - Project background, problem statement, and proposed solution
- [Hardware](design/hardware) - V1 -> V2 design iteration, sensor mapping, and V3 roadmap
- [Modeling](design/modeling) - ODE kinetics, FBA, and fermentation simulation
- [Software](design/software) - Lab data system, Wiki, and dashboard
- [Implementation](implementation) - Wet-lab workflow and timeline
- [Results](results) - Experimental outcomes (updated after wet-lab)
- [Contribution](contribution) - Open-source contributions and GitHub releases
- [Team](team) - Member bios and roles
- [Attributions](attributions) - Sponsors, advisors, and acknowledgements

---

## Contact

- **Team lead**: Thomas ZHAO (赵昶瑞)
- **School**: Shanghai Hongwen School Pudong
- **Track**: iGEM 2026
