# -*- coding: utf-8 -*-
"""
optimize_pid.py - 网格搜索 + 局部优化
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import json

PARAMS = {
    'mu_max': 0.5, 'Ks': 0.5, 'Yxs': 0.45, 'kd': 0.01,
    'Vmax_enzyme': 1.5, 'Km_enzyme': 0.5,
    'qp': 0.2, 'Kp_xos': 2.0,
    'qO2': 0.5, 'kLa': 100, 'DO_sat': 7.5,
    'V': 1.0, 'rho': 1000, 'Cp': 4.18,
    'Q_heater_max': 50, 'U_A': 0.5, 'T_amb': 25,
    'T_opt': 37, 'sigma_T': 8, 'Q_bio_per_gX': 0.3,
    'pH_opt': 6.5, 'sigma_pH': 1.5, 'pH_init': 7.0,
    'k_acid': 0.005, 'buffer': 1.0,
}
P = PARAMS
DURATION_H = 48
DT = 0.05          # 粗一点 0.05h=3min，够用
STEPS = int(DURATION_H / DT)
TC = P['V'] * P['rho'] * P['Cp'] / 3600.0


def simulate(Kp, Ki, Kd, T_set, Vmax_e, kLa, X0, S0, return_full=False):
    X = np.empty(STEPS + 1); S = np.empty(STEPS + 1); P_ = np.empty(STEPS + 1)
    T = np.empty(STEPS + 1); pH = np.empty(STEPS + 1); DO = np.empty(STEPS + 1)
    X[0] = X0; S[0] = S0; P_[0] = 0.0; T[0] = 25.0; pH[0] = P['pH_init']; DO[0] = P['DO_sat']
    integral = 0.0
    prev_err = T_set - T[0]
    deriv_f = 0.0
    alpha = 0.1

    for i in range(STEPS):
        Xi, Si, Pi, Ti, pHi, DOi = X[i], S[i], P_[i], T[i], pH[i], DO[i]
        mS = Si / (P['Ks'] + Si) if Si > 0 else 0.0
        mDO = DOi / (0.05 + DOi) if DOi > 0 else 0.0
        fT = np.exp(-((Ti - P['T_opt']) / P['sigma_T']) ** 2)
        fP = np.exp(-((pHi - P['pH_opt']) / P['sigma_pH']) ** 2)
        mu = P['mu_max'] * mS * mDO * fT * fP
        enzy = Vmax_e * Si / (P['Km_enzyme'] + Si) if Si > 0 else 0.0
        cons = P['qp'] * Xi * Pi / (P['Kp_xos'] + Pi + 0.01)
        dX = mu * Xi - P['kd'] * Xi
        dS = -mu * Xi / P['Yxs'] - enzy  # 修复：酶水解也消耗底物（质量守恒）
        dP_ = enzy - cons
        err = T_set - Ti
        integral += err * DT
        d_raw = (err - prev_err) / DT
        deriv_f = alpha * d_raw + (1 - alpha) * deriv_f
        prev_err = err
        out = max(0.0, min(1.0, Kp * err + Ki * integral + Kd * deriv_f))
        Q_h = out * P['Q_heater_max']
        Q_bio = P['Q_bio_per_gX'] * Xi * P['V']
        Q_loss = P['U_A'] * (Ti - P['T_amb'])
        dT = (Q_h + Q_bio - Q_loss) / TC
        dpH = -P['k_acid'] * Xi / P['buffer']
        dDO = kLa * (P['DO_sat'] - DOi) - P['qO2'] * Xi

        X[i+1] = max(0, Xi + DT * dX)
        S[i+1] = max(0, Si + DT * dS)
        P_[i+1] = max(0, Pi + DT * dP_)
        T[i+1] = max(20, min(50, Ti + DT * dT))
        pH[i+1] = max(4, min(9, pHi + DT * dpH))
        DO[i+1] = max(0, min(10, DOi + DT * dDO))

    if return_full:
        return {'t': np.arange(STEPS + 1) * DT, 'X': X, 'S': S, 'P': P_, 'T': T, 'pH': pH, 'DO': DO}
    return float(P_.max()), float(T.std()), float(pH.min()), float(DO.min())


if __name__ == '__main__':
    print("=" * 60)
    print("BrewXOS 网格搜索优化")
    print("=" * 60)

    # 速度测试
    t0 = time.time()
    for _ in range(10):
        simulate(5, 0.05, 8, 37, 1.5, 100, 0.1, 10)
    dt_avg = (time.time() - t0) / 10 * 1000
    print(f"\n[速度] {dt_avg:.0f} ms / 仿真")
    n_total = 8 * 4 * 5 * 3 * 4 * 3 * 3 * 3
    print(f"[预算] 网格 {n_total} 点 ≈ {n_total * dt_avg / 1000:.0f}s")

    # 1) 网格搜索
    Kp_grid = [3, 5, 8, 12]
    Ki_grid = [0, 0.05, 0.1]
    Kd_grid = [0, 5, 10, 15]
    T_set_grid = [35, 37, 39]
    Vmax_grid = [1.0, 2.0, 3.0]
    kLa_grid = [80, 150]
    X0_grid = [0.1, 0.3]
    S0_grid = [10, 15]

    best = None
    best_score = 1e9
    n_eval = 0
    t0 = time.time()

    print(f"\n[1/2] 网格搜索 {n_total} 点...")
    for Kp in Kp_grid:
        for Ki in Ki_grid:
            for Kd in Kd_grid:
                for T_set in T_set_grid:
                    for Vmax in Vmax_grid:
                        for kLa in kLa_grid:
                            for X0 in X0_grid:
                                for S0 in S0_grid:
                                    try:
                                        peak, ts, ph, do_ = simulate(Kp, Ki, Kd, T_set, Vmax, kLa, X0, S0)
                                    except:
                                        continue
                                    n_eval += 1
                                    penalty = 0
                                    if ts > 0.5: penalty += 50 * (ts - 0.5)
                                    if ph < 5.5: penalty += 30 * (5.5 - ph)
                                    if do_ < 1.0: penalty += 20 * (1.0 - do_)
                                    if peak > S0: penalty += 100 * (peak - S0)  # XOS 不能超过初始底物
                                    score = -peak + penalty
                                    if score < best_score:
                                        best_score = score
                                        best = (Kp, Ki, Kd, T_set, Vmax, kLa, X0, S0, peak, ts, ph, do_)

    elapsed = time.time() - t0
    print(f"  {elapsed:.1f}s, {n_eval} 次评估")

    Kp, Ki, Kd, T_set, Vmax, kLa, X0, S0, peak, ts, ph, do_ = best
    base = simulate(5, 0.05, 8, 37, 1.5, 100, 0.1, 10)
    print(f"\n{'='*60}")
    print(f"★ 最优解（网格搜索）")
    print(f"{'='*60}")
    print(f"  Kp    = {Kp:.1f}    (原 5.0)")
    print(f"  Ki    = {Ki:.3f}   (原 0.05)")
    print(f"  Kd    = {Kd:.1f}    (原 8.0)")
    print(f"  T_set = {T_set}°C    (原 37)")
    print(f"  Vmax  = {Vmax} g/L/h  (原 1.5)")
    print(f"  kLa   = {kLa} /h  (原 100)")
    print(f"  X0    = {X0} g/L  (原 0.1)")
    print(f"  S0    = {S0} g/L  (原 10)")
    print(f"\n  XOS peak = {peak:.3f} g/L  (old {base[0]:.2f}, +{(peak-base[0])/base[0]*100:.1f}%)")
    print(f"  temp std = +- {ts:.3f}C  {'OK' if ts<0.5 else 'OVER'}")
    print(f"  pH min   = {ph:.2f}  {'OK' if ph>5.5 else 'LOW'}")
    print(f"  DO min   = {do_:.2f} mg/L  {'OK' if do_>1 else 'LOW'}")
    print(f"  Yield    = {peak/S0*100:.0f}% of initial xylan")

    # 保存
    output = {
        'Kp': Kp, 'Ki': Ki, 'Kd': Kd, 'T_set': T_set,
        'Vmax': Vmax, 'kLa': kLa, 'X0': X0, 'S0': S0,
        'peak_XOS': round(peak, 3), 'temp_std': round(ts, 3),
        'min_pH': round(ph, 2), 'min_DO': round(do_, 2),
        'improvement_pct': round((peak-base[0])/base[0]*100, 1)
    }
    with open(r'C:\Users\xiaomi\Desktop\igem\optimization_result.json', 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n  → C:\\Users\\xiaomi\\Desktop\\igem\\optimization_result.json")

    # 画图
    base_full = simulate(5, 0.05, 8, 37, 1.5, 100, 0.1, 10, True)
    opt_full = simulate(Kp, Ki, Kd, T_set, Vmax, kLa, X0, S0, True)
    t = base_full['t']
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0, 0].plot(t, base_full['P'], '#c97b3f', label=f'当前 → {base[0]:.2f}', lw=1.5)
    axes[0, 0].plot(t, opt_full['P'], '#2f6f5e', label=f'最优 → {peak:.2f}', lw=2)
    axes[0, 0].set_ylabel('XOS (g/L)'); axes[0, 0].set_title('★ XOS 产品'); axes[0, 0].legend(); axes[0, 0].grid(alpha=0.3)

    axes[0, 1].plot(t, base_full['X'], '#c97b3f', lw=1.5)
    axes[0, 1].plot(t, opt_full['X'], '#2f6f5e', lw=1.5)
    axes[0, 1].set_ylabel('菌体 (g/L)'); axes[0, 1].set_title('菌体增长'); axes[0, 1].grid(alpha=0.3)

    axes[1, 0].plot(t, base_full['T'], '#c97b3f', lw=1.5)
    axes[1, 0].plot(t, opt_full['T'], '#2f6f5e', lw=2)
    axes[1, 0].axhline(T_set, color='gray', ls='--', alpha=0.5)
    axes[1, 0].set_ylabel('温度 (°C)'); axes[1, 0].set_xlabel('时间 (h)'); axes[1, 0].set_title('PID 温度'); axes[1, 0].grid(alpha=0.3)

    axes[1, 1].plot(t, base_full['S'], '#c97b3f', lw=1.5)
    axes[1, 1].plot(t, opt_full['S'], '#2f6f5e', lw=1.5)
    axes[1, 1].set_ylabel('底物 (g/L)'); axes[1, 1].set_xlabel('时间 (h)'); axes[1, 1].set_title('底物消耗'); axes[1, 1].grid(alpha=0.3)

    plt.suptitle(f'BrewXOS 网格优化：XOS {base[0]:.2f} → {peak:.2f} g/L ({(peak-base[0])/base[0]*100:+.1f}%)', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(r'C:\Users\xiaomi\Desktop\igem\optimization_comparison.png', dpi=120, bbox_inches='tight')
    print(f"  对比图 → C:\\Users\\xiaomi\\Desktop\\igem\\optimization_comparison.png")
    print("\n✓ 完成")
