"""
BrewXOS Metabolic Pathway Model v1.0 (2026-09-07)

扩展 wiki/results.md §2.1 的 6 状态 ODE (X/S/P/T/pH/DO) 为 9 状态完整代谢通路:
  Xylan → Xylose → XOS (工程菌 xylanase 催化) → SCFA (益生菌 Bifidobacterium 发酵)

状态 (g/L or unit):
  0 Xylan       木聚糖底物 (BSG 提取物)
  1 Xylose      木糖中间产物
  2 XOS         木寡糖目标产物
  3 X_eng       工程菌 (Bacillus subtilis WB800 分泌 xylanase)
  4 X_bifido    益生菌 (Bifidobacterium longum)
  5 SCFA        短链脂肪酸 (acetate + propionate + butyrate 合计)
  6 T           温度 (°C)
  7 pH          pH
  8 DO          溶解氧 (mg/L)

动力学:
  - xylan → xylose: Michaelis-Menten (K_m, V_max 来自 Kulkarni 1999 Bacillus)
  - xylose → XOS: transxylosylation (简化为一阶, yield=0.95)
  - 工程菌生长: Monod (xylan 限制, Arrhenius 温度补偿)
  - 益生菌生长: Monod (XOS 限制)
  - 益生菌代谢 XOS → SCFA: 1阶 + 产物 SCFA 抑制
  - 温度: 1阶 RC 模型 (跟 v3.1/v3.2 PID 控制一致)
  - pH: 1阶 (acid/base 反馈, 目标 6.5)
  - DO: 1阶 (曝气 + 菌消耗)

求解: scipy.integrate.solve_ivp (LSODA, 48h horizon, 0.01h step)
参考: day2_enzyme_hydrolysis.py + wiki/design/modeling_comparison.md
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import os
import json
from datetime import datetime

# ============================================================
# 参数 (来自文献 + 估计值)
# ============================================================

# 工程菌: Bacillus subtilis WB800 表达 xylanase (Kulkarni 1999 framework + Liu 2011 hyper-secreting)
P_eng = {
    'mu_max':     0.45,    # 最大比生长速率 (1/h) - Bacillus 文献典型
    'K_xylan':    0.5,     # Monod 半饱和常数 (g/L)
    'Y_eng':      0.30,    # 菌体得率 (g X / g xylan consumed)
    'X_max':      5.0,     # 最大菌浓 (g/L) - 营养/空间限制
    'k_death':    0.01,    # 死亡率 (1/h) - 维持代谢
    'T_opt':      37.0,    # 最适温度 (°C)
    'pH_opt':     6.5,     # 最适 pH
    'T_range':    8.0,     # 温度适应宽度 (°C)
    'pH_range':   1.0,     # pH 适应宽度
    'xylanase_kcat': 22.0, # xylanase V_max (U/mg protein) - Kulkarni 1999
    'Km_xylanase': 3.2,    # xylanase K_m (mg/mL) - Kulkarni 1999
    'Ki_XOS':     0.5,     # 产物 XOS 抑制常数 (g/L)
    'q_xylanase': 0.5,     # 比 xylanase 分泌速率 (U/mg/h) - Liu 2011 估计
}

# 益生菌: Bifidobacterium longum (肠道益生菌, XOS 发酵产生 SCFA)
P_bifido = {
    'mu_max':     0.30,    # 最大比生长速率 (1/h)
    'K_XOS':      0.8,     # Monod 半饱和常数 (g/L)
    'Y_bifido':   0.18,    # 菌体得率 (g X / g XOS consumed)
    'X_bifido_max': 4.0,   # 最大菌浓 (g/L)
    'T_opt_bifido': 37.0,  # 最适温度
    'pH_opt_bifido': 6.0,  # 最适 pH
    'T_range_bifido': 6.0, # 温度适应宽度
    'pH_range_bifido': 1.5, # pH 适应宽度
    'Y_SCFA':     0.42,    # SCFA 得率 (g SCFA / g XOS consumed) - 文献典型
}

# 环境控制 (PID v3.2 目标值)
P_env = {
    'T_set':      37.0,    # 温度设定点 (°C)
    'pH_set':     6.5,     # pH 设定点
    'DO_set':     4.0,     # DO 设定点 (mg/L) - 微好氧
    # 1阶 RC 模型参数 (跟 sim_v3_1_vs_v3_2.py 一致)
    'C_thermal':  200.0,   # 热容 (J/°C)
    'h_thermal':  0.5,     # 热损 (W/°C)
    'T_amb':      25.0,    # 环境温度
    'P_heater':   30.0,    # 加热功率 (W)
    # pH 缓冲
    'pH_buffer':  0.3,     # pH 控制响应 (1/h)
    # DO 曝气
    'k_O2_in':    15.0,    # 曝气 (mg/L/h)
    'k_O2_out':   0.5,     # 表面溢出 (1/h)
}

# 初始条件
IC = {
    'Xylan':     10.0,     # g/L (BSG 提取物, 24h 批次)
    'Xylose':    0.0,
    'XOS':       0.0,
    'X_eng':     0.10,     # g/L (10% 接种)
    'X_bifido':  0.0,      # 益生菌后接种 (12h 后)
    'SCFA':      0.0,
    'T':         30.0,     # 初始温度
    'pH':        7.0,      # 初始 pH
    'DO':        7.0,      # mg/L
}

# 仿真时长
T_HORIZON = 48.0    # h
DT_OUT = 0.1         # 输出步长 (h)


# ============================================================
# ODE 系统
# ============================================================

def arrhenius_factor(T, T_opt, T_range):
    """温度响应: Arrhenius-like bell curve"""
    return np.exp(-((T - T_opt) / T_range) ** 2)

def pH_factor(pH, pH_opt, pH_range):
    """pH 响应: bell curve"""
    return np.exp(-((pH - pH_opt) / pH_range) ** 2)

def monod(S, K_S):
    """Monod 生长动力学"""
    return S / (K_S + S + 1e-9)

def michaelis_menten_inhibited(S, V_max, K_m, K_i, I):
    """产物抑制 Michaelis-Menten: v = V_max * S / (K_m + S + S^2/K_i)
    (保留以备后续 FBA 使用, v1.0 路径用简化版)"""
    if K_i < 1e-6:
        return V_max * S / (K_m + S + 1e-9)
    return V_max * S / (K_m + S + S * S / K_i)

def pathway_ode(t, y, P_eng, P_bifido, P_env, IC):
    """9 状态代谢通路 ODE

    Args:
        t: 时间 (h)
        y: [Xylan, Xylose, XOS, X_eng, X_bifido, SCFA, T, pH, DO]
    """
    Xylan, Xylose, XOS, X_eng, X_bifido, SCFA, T, pH, DO = y

    # --- 保护: 浓度不能为负 ---
    Xylan     = max(Xylan, 0)
    Xylose    = max(Xylose, 0)
    XOS       = max(XOS, 0)
    X_eng     = max(X_eng, 0)
    X_bifido  = max(X_bifido, 0)
    SCFA      = max(SCFA, 0)
    T         = np.clip(T, 20, 50)
    pH        = np.clip(pH, 4, 9)
    DO        = max(DO, 0)

    # --- 温度/pH 影响因子 ---
    f_T_eng   = arrhenius_factor(T, P_eng['T_opt'], P_eng['T_range'])
    f_pH_eng  = pH_factor(pH, P_eng['pH_opt'], P_eng['pH_range'])
    f_T_bif   = arrhenius_factor(T, P_bifido['T_opt_bifido'], P_bifido['T_range_bifido'])
    f_pH_bif  = pH_factor(pH, P_bifido['pH_opt_bifido'], P_bifido['pH_range_bifido'])

    # --- 工程菌: xylanase 酶水解 (Michaelis-Menten + 产物抑制) ---
    # 简化: v_xylanase (g/L/h) = q_xylanase * X_eng * monod(xylan, Km) * f_T * f_pH / (1 + XOS/Ki)
    # 标定: q_xylanase = 0.6 g XOS / g X_eng / h (在饱和底物+无抑制+T_opt+pH_opt)
    # 这对应 Bacillus WB800 文献典型分泌量
    v_xylanase = P_eng['q_xylanase'] * X_eng * monod(Xylan, P_eng['Km_xylanase']) * f_T_eng * f_pH_eng
    v_xylanase = v_xylanase / (1.0 + XOS / P_eng['Ki_XOS'])
    v_xylanase = max(v_xylanase, 0)

    # --- 工程菌生长 (Monod, xylan 限制) ---
    mu_eng = P_eng['mu_max'] * monod(Xylan, P_eng['K_xylan']) * f_T_eng * f_pH_eng

    # --- 木糖 → XOS (transxylosylation, 简化一阶) ---
    v_xylosyl = 0.8 * Xylose * f_T_eng * f_pH_eng  # 1阶
    v_xylosyl = max(v_xylosyl, 0)

    # --- 益生菌接种 (12h 后) ---
    bifido_inoculation = 0.0
    if 12.0 <= t <= 12.1 and X_bifido < 0.01:
        bifido_inoculation = 0.10  # g/L 一次性接种

    # --- 益生菌生长 (Monod, XOS 限制) ---
    mu_bifido = P_bifido['mu_max'] * monod(XOS, P_bifido['K_XOS']) * f_T_bif * f_pH_bif

    # --- 益生菌代谢 XOS → SCFA ---
    v_XOS_to_SCFA = (mu_bifido / P_bifido['Y_bifido'] + P_bifido['mu_max'] * 0.05) * X_bifido * f_T_bif * f_pH_bif

    # --- 工程菌死亡 + 益生菌死亡 ---
    dX_eng_death = P_eng['k_death'] * X_eng
    dX_bif_death = P_eng['k_death'] * X_bifido

    # ============================================================
    # 9 个 ODE (加 logistic cap 防止菌体指数爆炸)
    # ============================================================
    dXylan_dt    = -v_xylanase
    dXylose_dt   = v_xylanase - v_xylosyl
    dXOS_dt      = v_xylosyl * 0.95 - v_XOS_to_SCFA   # 95% yield

    # logistic growth: dX/dt = mu * X * (1 - X/X_max) - k_death * X
    # 高温死亡增强: k_death_eff = k_death * (1 + max(0, T-T_opt)/5)
    k_death_eng_eff  = P_eng['k_death'] * (1.0 + max(0, T - P_eng['T_opt']) / 5.0)
    k_death_bif_eff  = P_eng['k_death'] * (1.0 + max(0, T - P_bifido['T_opt_bifido']) / 5.0)
    dX_eng_dt    = mu_eng * X_eng * (1 - X_eng / P_eng['X_max']) - k_death_eng_eff * X_eng
    dX_bifido_dt = mu_bifido * X_bifido * (1 - X_bifido / P_bifido['X_bifido_max']) - k_death_bif_eff * X_bifido + bifido_inoculation
    dSCFA_dt     = v_XOS_to_SCFA * P_bifido['Y_SCFA']

    # --- 温度 (1阶 RC, PID 控 37°C, 跟 v3.1/v3.2 一致) ---
    # Bang-bang 加热: T < T_set - 0.2 全开, T > T_set + 0.5 关 (Peltier 介入)
    if T < P_env['T_set'] - 0.2:
        Q_in = P_env['P_heater']  # 全功率加热 30W
    elif T > P_env['T_set'] + 0.5:
        Q_in = 0  # 关加热 (Peltier 冷却, 跟 v3.2 一致)
    else:
        Q_in = P_env['P_heater'] * 0.3  # 死区维持
    Q_loss = P_env['h_thermal'] * (T - P_env['T_amb'])
    # 微生物代谢放热 (∝ μ·X, logistic cap 后不会爆炸)
    Q_micro = 5.0 * (mu_eng * X_eng + mu_bifido * X_bifido)
    dT_dt = (Q_in - Q_loss + Q_micro) / P_env['C_thermal']

    # --- pH (1阶缓冲控制到 6.5) ---
    # SCFA 累积导致 pH 下降
    pH_drift = -0.05 * SCFA  # SCFA 1 g/L 引起 pH 下降
    pH_control = P_env['pH_buffer'] * (P_env['pH_set'] - pH)
    dpH_dt = pH_drift + pH_control

    # --- DO (曝气 - 菌消耗) ---
    O2_in = P_env['k_O2_in'] * (1.0 - DO / 8.0)  # 饱和 8 mg/L
    O2_out = P_env['k_O2_out'] * DO
    O2_consume = 0.5 * (mu_eng * X_eng + mu_bifido * X_bifido)  # 菌呼吸 (μX 体积呼吸, 不会随 X 爆炸因为 logistic cap)
    dDO_dt = O2_in - O2_out - O2_consume
    # DO 物理约束 ≥ 0
    if dDO_dt < 0 and DO <= 0:
        dDO_dt = 0

    return [dXylan_dt, dXylose_dt, dXOS_dt, dX_eng_dt, dX_bifido_dt,
            dSCFA_dt, dT_dt, dpH_dt, dDO_dt]


# ============================================================
# 仿真
# ============================================================

def run_simulation():
    print("=" * 60)
    print("BrewXOS Pathway Model v1.0 (2026-09-07)")
    print(f"9-state ODE: Xylan→Xylose→XOS→SCFA + 工程菌 + 益生菌 + T/pH/DO")
    print(f"Horizon: {T_HORIZON} h, output step: {DT_OUT} h")
    print("=" * 60)

    y0 = [IC['Xylan'], IC['Xylose'], IC['XOS'], IC['X_eng'], IC['X_bifido'],
          IC['SCFA'], IC['T'], IC['pH'], IC['DO']]

    sol = solve_ivp(
        pathway_ode,
        (0, T_HORIZON),
        y0,
        args=(P_eng, P_bifido, P_env, IC),
        method='LSODA',
        t_eval=np.arange(0, T_HORIZON + DT_OUT, DT_OUT),
        max_step=0.1,
        rtol=1e-6,
        atol=1e-9
    )

    if not sol.success:
        raise RuntimeError(f"ODE failed: {sol.message}")

    df = pd.DataFrame(sol.y.T, columns=[
        'Xylan_gL', 'Xylose_gL', 'XOS_gL', 'X_eng_gL', 'X_bifido_gL',
        'SCFA_gL', 'T_C', 'pH', 'DO_mgL'
    ])
    df.insert(0, 't_h', sol.t)
    return df


def plot_results(df, out_png):
    """6 子图: Xylan/Xylose/XOS/SCFA + 工程菌/益生菌 + T/pH/DO"""
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle('BrewXOS Pathway Model v1.0 - 48h Simulation (T=37°C, pH=6.5)',
                 fontsize=14, fontweight='bold')

    # 1. 底物-产物通路
    ax = axes[0, 0]
    ax.plot(df.t_h, df.Xylan_gL, label='Xylan (substrate)', color='brown', linewidth=2)
    ax.plot(df.t_h, df.Xylose_gL, label='Xylose (intermediate)', color='orange', linestyle='--')
    ax.plot(df.t_h, df.XOS_gL, label='XOS (product)', color='green', linewidth=2)
    ax.plot(df.t_h, df.SCFA_gL, label='SCFA (downstream)', color='purple', linewidth=2)
    ax.axvline(x=12, color='gray', linestyle=':', alpha=0.6, label='Bifido inoculation (12h)')
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('Concentration (g/L)')
    ax.set_title('Metabolic Pathway: BSG → XOS → SCFA')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # 2. 微生物生长
    ax = axes[0, 1]
    ax.plot(df.t_h, df.X_eng_gL, label='B. subtilis (engineered)', color='blue', linewidth=2)
    ax.plot(df.t_h, df.X_bifido_gL, label='B. longum (probiotic)', color='red', linewidth=2)
    ax.axvline(x=12, color='gray', linestyle=':', alpha=0.6)
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('Biomass (g/L)')
    ax.set_title('Microbial Growth')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # 3. 温度
    ax = axes[1, 0]
    ax.plot(df.t_h, df.T_C, color='red', linewidth=2)
    ax.axhline(y=37, color='black', linestyle='--', alpha=0.5, label='Setpoint 37°C')
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('Temperature Control (PID v3.2)')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # 4. pH
    ax = axes[1, 1]
    ax.plot(df.t_h, df.pH, color='teal', linewidth=2)
    ax.axhline(y=6.5, color='black', linestyle='--', alpha=0.5, label='Setpoint 6.5')
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('pH')
    ax.set_title('pH Control (SCFA drift + buffer)')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # 5. DO
    ax = axes[2, 0]
    ax.plot(df.t_h, df.DO_mgL, color='navy', linewidth=2)
    ax.axhline(y=4, color='black', linestyle='--', alpha=0.5, label='Setpoint 4 mg/L')
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('DO (mg/L)')
    ax.set_title('Dissolved Oxygen (aeration)')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    # 6. 关键 yield 指标
    ax = axes[2, 1]
    conversion = (1 - df.Xylan_gL / IC['Xylan']) * 100
    xos_yield = df.XOS_gL / IC['Xylan'] * 100
    scfa_yield = df.SCFA_gL / IC['Xylan'] * 100
    ax.plot(df.t_h, conversion, label='Xylan→XOS conversion', color='green', linewidth=2)
    ax.plot(df.t_h, xos_yield, label='XOS yield (g XOS / g Xylan)', color='darkgreen', linewidth=2)
    ax.plot(df.t_h, scfa_yield, label='SCFA yield (downstream)', color='purple', linewidth=2)
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('Yield (%)')
    ax.set_title('Key Performance Indicators')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_png, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  PNG saved: {out_png}")


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. Run
    print("\n[1/3] Running 9-state ODE simulation...")
    df = run_simulation()

    # 2. Save CSV
    csv_out = os.path.join(out_dir, f'brewxos_pathway_v1_{ts}.csv')
    df.to_csv(csv_out, index=False)
    print(f"  CSV saved: {csv_out} ({len(df)} rows)")

    # 3. Plot
    print("\n[2/3] Generating plots...")
    png_out = os.path.join(out_dir, f'brewxos_pathway_v1_{ts}.png')
    plot_results(df, png_out)

    # 4. Summary metrics
    print("\n[3/3] Summary metrics at 48h:")
    final = df.iloc[-1]
    print(f"  Xylan consumed:   {IC['Xylan'] - final.Xylan_gL:.2f} g/L ({(1 - final.Xylan_gL/IC['Xylan'])*100:.1f}%)")
    print(f"  XOS produced:     {final.XOS_gL:.2f} g/L (yield {final.XOS_gL/IC['Xylan']*100:.1f}%)")
    print(f"  SCFA produced:    {final.SCFA_gL:.2f} g/L (downstream)")
    print(f"  Xylose residual:  {final.Xylose_gL:.2f} g/L")
    print(f"  B. subtilis:      {final.X_eng_gL:.2f} g/L")
    print(f"  B. longum:        {final.X_bifido_gL:.2f} g/L")
    print(f"  Final T:          {final.T_C:.1f}°C")
    print(f"  Final pH:         {final.pH:.2f}")
    print(f"  Final DO:         {final.DO_mgL:.2f} mg/L")

    # Save metrics JSON
    metrics = {
        'timestamp': ts,
        'horizon_h': T_HORIZON,
        'final': {
            'xylan_consumed_gL': round(IC['Xylan'] - final.Xylan_gL, 3),
            'conversion_pct': round((1 - final.Xylan_gL/IC['Xylan'])*100, 2),
            'xos_produced_gL': round(final.XOS_gL, 3),
            'xos_yield_pct': round(final.XOS_gL/IC['Xylan']*100, 2),
            'scfa_produced_gL': round(final.SCFA_gL, 3),
            'xylose_residual_gL': round(final.Xylose_gL, 3),
            'x_eng_gL': round(final.X_eng_gL, 3),
            'x_bifido_gL': round(final.X_bifido_gL, 3),
            'T_C': round(final.T_C, 2),
            'pH': round(final.pH, 2),
            'DO_mgL': round(final.DO_mgL, 2),
        },
        'parameters': {
            'engineered_strain': 'Bacillus subtilis WB800 (xylanase+)',
            'probiotic_strain': 'Bifidobacterium longum',
            'xylanase_kcat_U_mg': P_eng['xylanase_kcat'],
            'Km_xylanase_mg_mL': P_eng['Km_xylanase'],
            'Ki_XOS_gL': P_eng['Ki_XOS'],
            'T_set_C': P_env['T_set'],
            'pH_set': P_env['pH_set'],
        }
    }
    json_out = os.path.join(out_dir, f'brewxos_pathway_v1_{ts}_metrics.json')
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"\n  Metrics JSON: {json_out}")
    print("\n" + "=" * 60)
    print("DONE. v1.0 9-state metabolic pathway ODE complete.")
    print("=" * 60)


if __name__ == '__main__':
    main()
