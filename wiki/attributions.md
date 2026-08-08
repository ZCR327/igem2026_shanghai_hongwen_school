# Attributions

> Per iGEM attribution requirements, this page acknowledges the specific contributions of each team member, advisor, sponsor, and external resource that made BrewXOS possible.

---

## 1. Student Contributions

### Thomas ZHAO (赵昶瑞)

| Area | Specific contribution |
|------|----------------------|
| **Project leadership** | Defined the BSG -> XOS problem framing; coordinated the team across wet-lab, hardware, modeling, and software sub-teams; managed the Wiki freeze and GitHub release schedule |
| **Modeling** | Built the dynamic fermentation models in Python: Michaelis-Menten xylanase kinetics, FBA flux analysis using COBRApy + iJO1366 baseline, and dynamic ODE simulations in SciPy. Modeled 4 stages: BSG pretreatment, enzymatic hydrolysis, engineered B. subtilis fermentation, and gut microbiota fermentation of XOS |
| **Software** | Wrote the Flask + SQLite lab data system (BSG batch tracking, pretreatment log, hydrolysis log, fermentation log). Built the Wiki (Flask + Markdown rendering) and the Web dashboard scaffold (Vue + ECharts). Wrote the public GitHub release pipeline (commit conventions, .gitignore, README, MIT license) |
| **Hardware design** | Co-designed the V1 bioreactor enclosure (242 KB STEP) and the V2 sealed, modularized enclosure (458 KB STEP) in Autodesk Fusion 360. Designed the 6-parameter LCD dashboard, the modular fermentation / control zoning, and the beveled base. Iterated the design in 16 hours from V1 to V2 with a real feedback loop |
| **CAD / documentation** | Produced all CAD screenshots and CAD-to-Markdown documentation. Wrote the Hardware Recommendations document (English version, both .md and .docx) for the iGEM Wiki and for other teams to replicate |
| **Wiki** | Wrote the home page, description, team, attributions, and hardware design pages. Designed the Wiki information architecture (5 main pages + 5 design sub-pages) |
| **FTC cross-team coordination** | The same engineering habits, public-code discipline, and team-coordination practice translate from FTC robotics (where the student helped coordinate 3 sister FTC teams at Shanghai Hongwen School) into iGEM BrewXOS |

### *[Other team members - to be added with specific roles]*

We will fill in the rest of the team contributions after the team roster is finalized. The team's typical division:

- **Wet-lab lead** - B. subtilis engineering, xylanase cloning, fermentation wet-lab work
- **Hardware fabrication lead** - 3D printing, sensor wiring, bioreactor assembly
- **Human Practices lead** - brewery partnerships, education outreach, Wiki copywriting
- **Wet-lab assistant** - media prep, sample collection, data entry

---

## 2. Advisor Contributions

### Engineering Mentor (from ivymaker) - *to be named*

| Area | Contribution |
|------|-------------|
| FTC robotics expertise | 4 years guiding Shanghai Hongwen School FTC teams (including Team 19606 "Riser", which holds 18 awards across 4 seasons including 4x Control Award) |
| Hardware design review | Provided iterative feedback on the V1 and V2 enclosure designs; advised on DFRduino Mega2560 + DFRobot sensor ecosystem integration |
| Cross-team coordination | Managed the loan-out of the student (Thomas ZHAO) between 3 sister FTC teams in 2025-2026, which directly informed the BrewXOS team's "cross-team collaboration" practice |
| Control-system guidance | Advised on PID temperature control, colorimetric sensing, and the modular control panel architecture |

### Biology / Wet-lab Advisor - *to be named*

| Area | Contribution |
|------|-------------|
| B. subtilis strain selection | Advised on the chassis choice (B. subtilis WB800 or equivalent) and the xylanase secretion strategy |
| Fermentation protocol design | Reviewed and refined the fermentation protocol: media composition, induction timing, sampling cadence |
| Lab safety | Approved the biosafety level 1 (BSL-1) protocol; provided training on B. subtilis handling and waste deactivation |

---

## 3. Institutional Support

### Shanghai Hongwen School Pudong

| Contribution | Detail |
|-------------|--------|
| Laboratory space | Provided BSL-1 wet-lab access for fermentation experiments |
| Meeting rooms | Weekly team meetings and Wiki-editing sessions |
| Faculty advisor coordination | Connected the team with the engineering mentor and biology advisor |
| Letter of support | Provided the institutional letter required for iGEM team registration |
| STEM infrastructure | The school's existing 3-FTC-team program (19606 / 24068 / 24306) and ivymaker partnership provided the engineering culture and 3D-printing / electronics workbench access that BrewXOS relies on |

### ivymaker

| Contribution | Detail |
|-------------|--------|
| Engineering mentor dispatch | Provided the dedicated engineering mentor who advises BrewXOS and the 3 FTC teams at Shanghai Hongwen School |
| Equipment access | Access to the ivymaker engineering education network's 3D printers, electronics workbench, and sensor library |
| FTC competition infrastructure | The 4-year FTC program that produced Team 19606 and the 2025-2026 FIRST World Championship qualification directly seeded the engineering mindset of the BrewXOS team |

---

## 4. Hardware and Software Sponsors

### DFRobot

| Contribution | Detail |
|-------------|--------|
| DFRduino Mega2560 | Main controller of the BrewXOS bioreactor |
| pH / DO sensor ecosystem | DFRobot's pH kit (USD 29.50 list) and analog DO kit (USD 169 list) are the reference sensor modules used in the cost estimate and design recommendations |
| Open hardware documentation | DFRobot's publicly available sensor specifications and Arduino library code accelerated our design |

We are not in a paid sponsorship relationship with DFRobot. Their hardware is recommended in our open-source design documentation because of its quality, ecosystem fit, and accessibility to other iGEM teams.

### Autodesk

| Contribution | Detail |
|-------------|--------|
| Fusion 360 | Free educational license used for all BrewXOS hardware design (V1, V2, and future V3) |

### Open-Source Software Used

| Tool | License | Use in BrewXOS |
|------|---------|----------------|
| **COBRApy** | GPL-3.0 | Metabolic flux balance analysis (FBA) for the engineered B. subtilis chassis |
| **SciPy** | BSD-3-Clause | ODE integration, parameter fitting, statistical analysis |
| **NumPy** | BSD-3-Clause | Numerical backbone of all modeling code |
| **pandas** | BSD-3-Clause | Data wrangling for fermentation time-series |
| **Matplotlib** | PSF-based | Static plots for the Wiki and the modeling report |
| **Flask** | BSD-3-Clause | Web framework for the Wiki + Lab data system + dashboard |
| **SQLite** | Public Domain | Local database for the lab data system |
| **Vue.js** | MIT | Frontend framework for the future web dashboard |
| **ECharts** | Apache-2.0 | Plotting library for the future web dashboard |
| **Arduino IDE** | GPL-2.0 | Programming the DFRduino Mega2560 controller |
| **OpenSCAD / Fusion 360** | Various open / free | Mechanical CAD and 3D-printing slicing |

We are deeply grateful to the maintainers of these tools and the broader open-source community.

---

## 5. Academic References and Inspirations

The following papers, theses, and online resources directly shaped the BrewXOS design:

### XOS production and prebiotic science
- Mussatto, S. I. (2014). "Brewer's spent grain: a valuable feedstock for industrial applications." *J. Sci. Food Agric.* 94(7), 1264-1275.
- Aachary, A. A., & Prapulla, S. G. (2011). "Xylo-oligosaccharides (XOS) as an emerging prebiotic." *Compr. Rev. Food Sci. Food Saf.* 10(1), 2-20.
- Gibson, G. R., et al. (2017). ISAPP consensus statement on the definition and scope of prebiotics. *Nat. Rev. Gastroenterol. Hepatol.* 14(8), 491-502.
- Rastall, R. A. (2010). "Functional oligosaccharides: application and manufacture." *Annu. Rev. Food Sci. Technol.* 1, 305-339.

### Xylanase enzymology and BSG pretreatment
- Polizeli, M. L. T. M., et al. (2005). "Xylanases from fungi: properties and industrial applications." *Appl. Microbiol. Biotechnol.* 67(5), 577-591.
- Liu, M. Q., et al. (2011). "Engineering of a B. subtilis xylanase hyper-secreting strain." *Biotechnol. Bioeng.* 108(12), 2841-2851.

### Metabolic modeling with COBRApy
- Ebrahim, A., et al. (2013). "COBRApy: COnstraints-Based Reconstruction and Analysis for Python." *BMC Syst. Biol.* 7, 74.
- Orth, J. D., et al. (2010). "What is flux balance analysis?" *Nat. Biotechnol.* 28(3), 245-248.

### iGEM hardware and software inspiration
- Multiple MIT iGEM teams (2018-2023) for hardware + software stacks
- ETH Zurich iGEM 2019 for modeling documentation patterns

### FTC engineering culture
- FIRST Inspires - *de facto* open-source culture of robot design sharing
- Team 19606 "Riser" 4-year build log (we are the same school, see the FTC cross-pollination)

---

## 6. Industry Inspiration

- **Shandong Longlive Bio-Technology (China)**: largest Asian XOS producer. Their 4-step process (BSG -> xylan -> enzymatic hydrolysis -> XOS) is the industrial benchmark that BrewXOS aims to compress into 1 step.
- **Yufeng Industrial Group**: their xylanase strain library informed our choice of *B. subtilis* as a host.
- **International Prebiotic Association (IPA)**: their market data anchors the project impact estimates.

---

## 7. Open-Source Contributions Back to the Community

In the spirit of the iGEM open-source ethos, BrewXOS will release the following to the public:

| Deliverable | Format | License | Timeline |
|-------------|--------|---------|----------|
| BrewXOS bioreactor CAD (V1, V2, future V3) | STEP AP214 + screenshots | CC-BY-4.0 | Released 2026-08 |
| BrewXOS bioreactor bill of materials | Markdown + BOM spreadsheet | CC-BY-4.0 | Released 2026-08 |
| BrewXOS modeling code (COBRApy + SciPy) | Python scripts on GitHub | MIT | Released 2026-08 |
| BrewXOS lab data system (Flask + SQLite) | Python source | MIT | Released 2026-09 |
| BrewXOS wiki (Flask + Markdown) | Python source | MIT | Released 2026-09 |
| BrewXOS web dashboard (Vue + ECharts) | JavaScript source | MIT | Released 2026-10 |

**All of these are open-source and free for any team, school, or small brewery to replicate, modify, or build upon.**

---

## 8. Personal Acknowledgments

- **Thomas ZHAO** thanks the ivymaker engineering mentor for 2 years of patient FTC coaching that taught him how to ship engineering, not just study it.
- **The team** thanks Shanghai Hongwen School Pudong for trusting high school students with a real BSL-1 lab.
- **All of us** thank the iGEM organization for creating a worldwide community that makes ambitious student projects like this possible.
- **And a special thanks to the open-source community** - every line of code in BrewXOS stands on the shoulders of the maintainers of COBRApy, SciPy, Flask, Vue, and the thousand other libraries that make modern science happen.
