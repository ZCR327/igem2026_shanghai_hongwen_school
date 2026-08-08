# -*- coding: utf-8 -*-
"""
day2_enzyme_hydrolysis.py
BrewXOS Day 2 - Michaelis-Menten kinetics of xylanase on BSG-derived xylan.

This model simulates the enzymatic hydrolysis of xylan (extracted from
brewer's spent grain, BSG) into xylo-oligosaccharides (XOS) using a
fungal/bacterial xylanase. We use literature parameters for the kinetic
constants because our wet-lab strain is still in construction.

References:
  [1] Polizeli et al. (2005). Xylanases from fungi: properties and
      industrial applications. Appl Microbiol Biotechnol 67: 577-591.
  [2] Beg et al. (2001). Microbial xylanases and their industrial
      applications. Appl Microbiol Biotechnol 56: 326-338.
  [3] Kulkarni et al. (1999). Molecular and biotechnological aspects of
      xylanases. FEMS Microbiol Rev 23: 411-456.

iGEM contribution:
  - Demonstrates ODE-based modeling of a key reaction in BrewXOS
  - Compares parameter sets from 3 literature sources (sensitivity)
  - Includes a placeholder for the team's own future wet-lab data
  - Connects directly to the FTC PID control experience (curve fitting)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.optimize import curve_fit


# ---------------------------------------------------------------------------
# 1. Literature parameters (placeholder - replace with team wet-lab data)
# ---------------------------------------------------------------------------
LITERATURE_PARAMS = {
    'Polizeli_2005_Aspergillus': {
        'Km_mg_mL': 2.5,        # mg/mL (xylan)
        'Vmax_U_mg': 28.0,       # U/mg enzyme
        'T_opt_C': 45,           # degrees C
        'pH_opt': 5.5,
        'source': 'Polizeli et al. 2005, Appl Microbiol Biotechnol 67',
    },
    'Beg_2001_Trichoderma': {
        'Km_mg_mL': 1.8,
        'Vmax_U_mg': 35.0,
        'T_opt_C': 50,
        'pH_opt': 5.0,
        'source': 'Beg et al. 2001, Appl Microbiol Biotechnol 56',
    },
    'Kulkarni_1999_Bacillus': {
        'Km_mg_mL': 3.2,
        'Vmax_U_mg': 22.0,
        'T_opt_C': 37,
        'pH_opt': 6.5,
        'source': 'Kulkarni et al. 1999, FEMS Microbiol Rev 23',
    },
}

# Team wet-lab placeholder (to be filled in after our own strain is characterized)
TEAM_PARAMS = {
    'Km_mg_mL': None,    # TODO: replace with measured value
    'Vmax_U_mg': None,   # TODO: replace with measured value
    'T_opt_C': 37,       # Bacillus default
    'pH_opt': 6.5,
    'source': 'BrewXOS wet-lab (pending)',
}


# ---------------------------------------------------------------------------
# 2. Temperature dependence (Arrhenius)
# ---------------------------------------------------------------------------
def arrhenius_factor(T_C, T_opt_C, Ea_kJ_mol=42.0, R_kJ_mol_K=8.314e-3):
    """Arrhenius-like factor: peaks at T_opt, drops off at low/high T.
    Ea ~ 42 kJ/mol is typical for fungal xylanases."""
    T = T_C + 273.15
    T_opt = T_opt_C + 273.15
    # Simple two-sided Arrhenius
    f_low = np.exp(-Ea_kJ_mol / R_kJ_mol_K * (1.0 / T - 1.0 / T_opt))
    # Denaturation: empirical, doubles every 5 C above T_opt
    f_high = np.exp(-0.14 * (T_C - T_opt_C))
    return np.clip(f_low * f_high, 0, 1)


# ---------------------------------------------------------------------------
# 3. Michaelis-Menten ODE
# ---------------------------------------------------------------------------
def mm_ode(y, t, Km, Vmax, enzyme_mg_mL):
    """y = [S, P]  (substrate xylan, product XOS)
       Both in mg/mL.
    """
    S, P = y
    # Michaelis-Menten with product inhibition (competitive)
    Ki = 0.5  # mg/mL, product inhibition constant (literature typical)
    v = Vmax * enzyme_mg_mL * S / (Km * (1 + P / Ki) + S)
    dSdt = -v
    dPdt = 0.95 * v  # 95% of hydrolyzed xylan becomes XOS; 5% is xylose
    return [dSdt, dPdt]


def simulate_batch(Km, Vmax, enzyme_mg_mL, S0_mg_mL, t_hours=24, T_C=40):
    """Simulate a batch hydrolysis and return time, S, P arrays."""
    t = np.linspace(0, t_hours, 200)
    T_factor = arrhenius_factor(T_C, T_opt_C=40)
    Vmax_eff = Vmax * T_factor
    sol = odeint(mm_ode, [S0_mg_mL, 0.0], t, args=(Km, Vmax_eff, enzyme_mg_mL))
    return t, sol[:, 0], sol[:, 1]


# ---------------------------------------------------------------------------
# 4. Simulate all 3 literature strains + sensitivity sweep
# ---------------------------------------------------------------------------
def run_all_simulations():
    S0 = 10.0           # mg/mL initial xylan
    enzyme = 0.5        # mg/mL enzyme loading
    T_C = 40            # operating temperature
    t_hours = 24

    results = {}
    for name, p in LITERATURE_PARAMS.items():
        t, S, P = simulate_batch(p['Km_mg_mL'], p['Vmax_U_mg'], enzyme, S0, t_hours, T_C)
        results[name] = (t, S, P)
    return results


def plot_results(results, out_path):
    plt.figure(figsize=(10, 6))
    for name, (t, S, P) in results.items():
        plt.plot(t, P, label=f"{name} (Km={LITERATURE_PARAMS[name]['Km_mg_mL']}, Vmax={LITERATURE_PARAMS[name]['Vmax_U_mg']})", linewidth=2)
    plt.xlabel('Time (hours)', fontsize=12)
    plt.ylabel('XOS concentration (mg/mL)', fontsize=12)
    plt.title('BrewXOS Day 2: XOS production by xylanase - 3 literature strains', fontsize=13)
    plt.legend(loc='lower right', fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"Saved plot: {out_path}")


# ---------------------------------------------------------------------------
# 5. Temperature sensitivity sweep (for iGEM Hardware pH/T considerations)
# ---------------------------------------------------------------------------
def temperature_sensitivity(Km=2.5, Vmax=28.0):
    """Show how XOS production varies with operating temperature."""
    temps = np.arange(20, 70, 5)
    S0, enzyme, t_hours = 10.0, 0.5, 24
    xos_at_24h = []
    for T in temps:
        _, _, P = simulate_batch(Km, Vmax, enzyme, S0, t_hours, T)
        xos_at_24h.append(P[-1])

    plt.figure(figsize=(8, 5))
    plt.plot(temps, xos_at_24h, 'o-', linewidth=2, markersize=8)
    plt.axvline(40, color='gray', linestyle='--', alpha=0.5, label='Reference T = 40 C')
    plt.xlabel('Temperature (C)', fontsize=12)
    plt.ylabel('XOS at 24 h (mg/mL)', fontsize=12)
    plt.title('Temperature sensitivity (Polizeli 2005 params)', fontsize=13)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('day2_temperature_sensitivity.png', dpi=120)
    plt.close()
    print("Saved plot: day2_temperature_sensitivity.png")


# ---------------------------------------------------------------------------
# 6. Fit-to-data placeholder (for when wet-lab data arrives)
# ---------------------------------------------------------------------------
def fit_team_data(time_data, xos_data, Km_init=2.5, Vmax_init=28.0):
    """Fit our own wet-lab data to Michaelis-Menten. To be called once
    the team has measured substrate depletion or product formation curves."""
    def mm_predict(t, Km, Vmax):
        S0 = 10.0  # assumed initial xylan
        enzyme = 0.5
        T_C = 40
        _, _, P = simulate_batch(Km, Vmax, enzyme, S0, t.max(), T_C)
        return np.interp(t, np.linspace(0, t.max(), 200), P)
    popt, pcov = curve_fit(mm_predict, time_data, xos_data, p0=[Km_init, Vmax_init])
    Km_fit, Vmax_fit = popt
    print(f"Fitted Km = {Km_fit:.2f} mg/mL, Vmax = {Vmax_fit:.2f} U/mg")
    return Km_fit, Vmax_fit


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 60)
    print("BrewXOS Day 2 - Xylanase Kinetics (Michaelis-Menten)")
    print("=" * 60)

    # 1. Run all 3 literature strain simulations
    print("\n[1] Running 3 literature strain simulations...")
    results = run_all_simulations()
    plot_results(results, 'day2_literature_comparison.png')

    # 2. Temperature sensitivity
    print("\n[2] Running temperature sensitivity sweep...")
    temperature_sensitivity()

    # 3. Print summary
    print("\n[3] Summary:")
    for name, p in LITERATURE_PARAMS.items():
        _, S, P = results[name]
        print(f"  {name}: at 24h, S = {S[-1]:.2f} mg/mL (xylan left), "
              f"P = {P[-1]:.2f} mg/mL (XOS produced)")

    print("\n" + "=" * 60)
    print("Day 2 complete! Next: Day 3 - BSG pretreatment ODE + Arrhenius")
    print("=" * 60)

