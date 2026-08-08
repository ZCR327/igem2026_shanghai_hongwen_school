# Description

## 1. The Problem: An Unseen Waste Stream

Brewer's spent grain (BSG) is the **single largest by-product of the brewing industry**. Every year, the world produces approximately **39 million tons** of BSG - a moist, fibrous residue left over after mashing grains for beer. In most countries, BSG is treated as a low-value waste:

- **Landfill or incineration** is the dominant disposal route
- Spontaneous composting releases methane, a potent greenhouse gas
- Only ~30% is currently upgraded into low-value animal feed, where price competition with corn and soy limits profit

**The cost is real**: the brewing industry pays to *dispose of* a feedstock that is, in chemical terms, **one of the richest natural sources of xylan (a hemicellulose) on the planet**.

## 2. The Opportunity: Upcycling BSG into Prebiotics

Xylan from BSG can be enzymatically hydrolyzed (or microbially fermented) into **xylo-oligosaccharides (XOS)** - a high-value, soluble prebiotic that selectively feeds beneficial gut bacteria such as *Bifidobacterium* and *Lactobacillus*.

XOS has a market position distinct from common prebiotics such as inulin or FOS:

| Property | XOS | FOS | Inulin |
|----------|-----|-----|--------|
| pH stability (acid, heat) | High | Low | Medium |
| Effective dose (g/day) | 0.7-1.4 | 3-10 | 5-15 |
| Selective for *Bifido* | Yes | Yes | Partial |
| Global prebiotic market share | Growing | Mature | Mature |
| Selling price (USD/kg, food grade) | 25-60 | 8-20 | 4-12 |

**XOS commands 2-5x the price of FOS or inulin per kg** because of its tolerance to acidic, high-temperature processing - making it a premium ingredient for functional foods, infant formula, and dietary supplements.

The global prebiotic market was valued at **~USD 8 billion in 2025** and is projected to grow at ~10% CAGR through 2030. The XOS segment is the fastest-growing slice.

## 3. Why XOS is Hard to Make Cheaply Today

Industrial XOS production today relies on **autoclave-driven acid or alkaline hydrolysis** of xylan-rich biomass (corn cobs, birch wood xylan). This approach is:

- **Energy-intensive** (high-temperature, high-pressure steam)
- **Corrosive** (mineral acids damage reactors)
- **Poorly selective** (produces a wide DP distribution, hard to purify)
- **Carbon-intensive** (steam generation + waste acid neutralization)

Enzymatic xylanase-based hydrolysis is cleaner but is **slow, expensive, and not yet widely deployed at industrial scale**, because:

1. Bulk xylanase is costly (USD 50-200 per kg)
2. Process yields are limited by end-product inhibition
3. No integrated process exists that combines *BSG pretreatment* + *enzyme production* + *XOS hydrolysis* in one engineered cell

## 4. Our Solution: BrewXOS

BrewXOS addresses all three barriers by **engineering a single microbial chassis - *Bacillus subtilis* - to perform BSG pretreatment, xylanase secretion, and XOS release in one fermentation cycle.**

The three-stage process:

```
Stage 1: BSG pretreatment (alkaline or thermal, in the same bioreactor)
   BSG (raw brewery waste) -> solubilized xylan + lignin residue (filterable)

Stage 2: Engineered B. subtilis fermentation
   Solubilized xylan -> xylanase secreted by B. subtilis -> hydrolysis in situ
   -> xylo-oligosaccharides (XOS, DP 2-6)

Stage 3: Colorimetric monitoring + downstream recovery
   DNS reducing-sugar assay at 540 nm -> real-time XOS trend
   -> simple filtration/evaporation -> food-grade XOS
```

By **co-locating the three stages in one bioreactor with a single engineered strain**, we eliminate the need for:
- Purchased xylanase (the strain makes its own)
- A separate hydrolysis reactor
- Sterile transfers between vessels

## 5. How the Project Addresses the Three iGEM Judging Criteria

| iGEM criterion | Our contribution |
|----------------|-----------------|
| **Engineering success** | Functional bioreactor design (V1 -> V2 iteration) with 6-parameter real-time monitoring, integrated into a 50 x 50 x 50 cm enclosure |
| **Wet-lab success** | Engineered B. subtilis chassis producing secreted xylanase for in-situ BSG hydrolysis |
| **Dry-lab / modeling** | Michaelis-Menten kinetics, FBA flux analysis, and dynamic fermentation simulation in COBRApy + SciPy, with all code public on GitHub |

## 6. Goals and Deliverables

### Engineering goal
- Build a working 1-2 L BrewXOS bioreactor that runs BSG -> XOS end-to-end in under 48 hours.

### Modeling goal
- Build a validated ODE + FBA model that predicts xylanase secretion rate and XOS titer from BSG loading, with parameter sensitivity analysis.

### Software goal
- Open-source Lab data system (Flask + SQLite), Wiki (Markdown + Flask), and Web dashboard (Vue + ECharts) on GitHub.

### Education / Human Practices goal
- A publicly documented hardware design (CAD + Bill of Materials) that other iGEM teams, school labs, or small breweries can replicate for under USD 1500.

## 7. Why a Hardware-First Project is the Right Approach

Most iGEM projects stop at "the cells can do it in a flask". The leap from **flask to fermenter** is where most synthetic biology work stalls. BrewXOS deliberately invests in **hardware + modeling + software** alongside the wet-lab, because:

- The hardware makes the wet-lab reproducible (no more "we ran it once and it worked")
- The modeling makes the hardware interpretable (we know *why* each parameter matters)
- The software makes both portable (open-source data + open hardware + open modeling)

**This is the cycle that turns a student project into a deployable technology.**

## 8. Inspirations

- **Industrial XOS producers** (Shandong Longlive, Yufeng Industrial, Bioactive): we studied their process flow, then asked "what if the xylanase step was free and in-cell?"
- **MIT iGEM 2019-2021 cellulose teams**: their hardware + modeling stacks inspired our Lab system + COBRApy integration
- **Gut microbiome literature** (Gibson et al., 2017; Rastall, 2010): provided the prebiotic-bifidobacteria mechanism that drives the project's social impact

## 9. The Bigger Picture

If BrewXOS works, the **same chassis can be retargeted** at other hemicellulose-rich wastes: corn stover, sugar cane bagasse, rice husks. The platform is the chassis, not the substrate.

The vision: **a single open-source bioreactor + a single open-source strain**, run on whatever lignocellulosic waste a region produces, delivering a **local prebiotic supply chain** that is small enough for a school lab, cheap enough for a village cooperative, and sustainable enough for a planet.

---

## 10. References

- Mussatto, S. I. (2014). "Brewer's spent grain: a valuable feedstock for industrial applications." *J. Sci. Food Agric.* 94(7), 1264-1275.
- Aachary, A. A., & Prapulla, S. G. (2011). "Xylo-oligosaccharides (XOS) as an emerging prebiotic: microbial synthesis, utilization, and structural health benefits." *Compr. Rev. Food Sci. Food Saf.* 10(1), 2-20.
- Gibson, G. R., et al. (2017). "Expert consensus document: The International Scientific Association for Probiotics and Prebiotics (ISAPP) consensus statement on the definition and scope of prebiotics." *Nat. Rev. Gastroenterol. Hepatol.* 14(8), 491-502.
- Rastall, R. A. (2010). "Functional oligosaccharides: application and manufacture." *Annu. Rev. Food Sci. Technol.* 1, 305-339.
