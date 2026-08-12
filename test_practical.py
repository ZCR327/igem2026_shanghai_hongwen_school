# -*- coding: utf-8 -*-
"""快速验证实用版"""
import numpy as np
import sys

P = {'mu_max': 0.5, 'Ks': 0.5, 'Yxs': 0.45, 'kd': 0.01,
     'qp': 0.2, 'Kp_xos': 2.0, 'qO2': 0.5, 'DO_sat': 7.5,
     'V': 1.0, 'rho': 1000, 'Cp': 4.18,
     'Q_heater_max': 50, 'U_A': 0.5, 'T_amb': 25,
     'T_opt': 37, 'sigma_T': 8, 'Q_bio_per_gX': 0.3,
     'pH_opt': 6.5, 'sigma_pH': 1.5, 'pH_init': 7.0,
     'k_acid': 0.005, 'buffer': 1.0, 'Km_enzyme': 0.5}
TC = P['V'] * P['rho'] * P['Cp'] / 3600.0
DT = 0.05
STEPS = int(48 / DT)

def run(name, Kp, Ki, Kd, T_set, Vmax_e, kLa, X0, S0):
    y = [X0, S0, 0.0, 25.0, P['pH_init'], P['DO_sat']]
    integral, prev_err, deriv_f = 0, T_set - y[3], 0
    alpha = 0.1
    for i in range(STEPS):
        X, S, XOS, T, pH, DO = y
        mS = S / (P['Ks'] + S) if S > 0 else 0
        mDO = DO / (0.05 + DO) if DO > 0 else 0
        fT = np.exp(-((T - P['T_opt']) / P['sigma_T']) ** 2)
        fP = np.exp(-((pH - P['pH_opt']) / P['sigma_pH']) ** 2)
        mu = P['mu_max'] * mS * mDO * fT * fP
        enzy = Vmax_e * S / (P['Km_enzyme'] + S) if S > 0 else 0
        cons = P['qp'] * X * XOS / (P['Kp_xos'] + XOS + 0.01)
        dX = mu * X - P['kd'] * X
        dS = -mu * X / P['Yxs'] - enzy
        dXOS = enzy - cons
        err = T_set - T
        integral += err * DT
        d_raw = (err - prev_err) / DT
        deriv_f = alpha * d_raw + 0.9 * deriv_f
        prev_err = err
        out = max(0, min(1, Kp * err + Ki * integral + Kd * deriv_f))
        Q_h = out * P['Q_heater_max']
        Q_bio = P['Q_bio_per_gX'] * X * P['V']
        Q_loss = P['U_A'] * (T - P['T_amb'])
        dT = (Q_h + Q_bio - Q_loss) / TC
        dpH = -P['k_acid'] * X / P['buffer']
        dDO = kLa * (P['DO_sat'] - DO) - P['qO2'] * X
        y = [max(0, X + DT * dX), max(0, S + DT * dS), max(0, XOS + DT * dXOS),
             max(20, min(50, T + DT * dT)), max(4, min(9, pH + DT * dpH)),
             max(0, min(10, DO + DT * dDO))]

    X_final, S_final, XOS_final, T_final, pH_final, DO_final = y
    # 找 peak XOS（用整个时序）
    return name, XOS_final, T_final, pH_final, DO_final

# 跑 5 个版本对比
versions = [
    ("baseline 5/0.05/8  37  1.5  100  0.1  10", 5, 0.05, 8, 37, 1.5, 100, 0.1, 10),
    ("zhao     5/0.05/8  37  1.5  100  0.1  10", 5, 0.05, 8, 37, 1.5, 100, 0.1, 10),
    ("optimal  3/0.05/0  35  3.0  80   0.1  15", 3, 0.05, 0, 35, 3.0, 80, 0.1, 15),
    ("practicl 3/0.05/5  37  2.0  120  0.1  12", 3, 0.05, 5, 37, 2.0, 120, 0.1, 12),
    ("safe     5/0.05/10 37  1.5  150  0.1  12", 5, 0.05, 10, 37, 1.5, 150, 0.1, 12),
]

print(f"{'Name':<40} {'XOS':>7} {'T':>6} {'pH':>5} {'DO':>6}")
print("-" * 70)
for v in versions:
    name, *args = v
    rname, xos, t, ph, do_ = run(name, *args)
    print(f"{rname:<40} {xos:>6.2f}  {t:>5.1f}  {ph:>4.2f}  {do_:>5.2f}")
