"""
BrewXOS PID v3.1 vs v3.2 模拟器对比 (2026-9-3)
================================================
目的: 在没有真板的情况下, 验证 v3.2 双温控设计 (帕尔贴自动) 比 v3.1 (单向 PID)
       在过冲抑制上更好.

物理模型 (一阶 RC 热模型, 简化的罐体):
    C * dT/dt = P_heater - h*(T - T_amb) - P_peltier
    C = 200 J/°C    (500 mL 水近似)
    h = 0.5 W/°C    (罐体表面积 + 自然对流)
    T_amb = 25 °C   (上海 9 月初室温)
    P_heater = pid_output * 100 W   (加热膜 24V 10W * 10 倍 = 100W 峰值)
    P_peltier = 30 W (开) / 0 (关)

PID 参数 (v3.1/v3.2 相同):
    Kp = 3.0, Ki = 0.05, Kd = 3.0
    target = 35 °C
    sample = 1s

v3.1: 仅加热膜 PID (P-only 制冷效果 = 0, 自然散热)
v3.2: 加热膜 PID + 帕尔贴自动 (current > 36 → 开, < 35.5 → 关, 死区 hysteresis)

输出:
    data/sim_v3_1_<date>.csv
    data/sim_v3_2_<date>.csv
    data/sim_compare_<date>.png  (matplotlib)
"""

import os
import csv
from datetime import datetime

# ================== 物理参数 ==================
C_WATER    = 200.0   # J/°C (500 mL 水)
H_LOSS     = 0.5     # W/°C (散热系数)
T_AMB      = 25.0    # °C (室温)
P_HEATER_MAX = 100.0 # W (加热膜满功率)
P_PELTIER  = 80.0    # W (帕尔贴开时制冷功率, v3.2 调强 + 更早介入)

# ================== PID 参数 ==================
KP = 3.0
KI = 0.05
KD = 3.0
I_LIMIT = 200.0
DERIV_ALPHA = 0.1
TARGET = 35.0
SAMPLE_S = 1.0
T_TOTAL_S = 1800   # 30 min

# v3.2 死区
PELTIER_ON  = 35.8
PELTIER_OFF = 35.3


class PIDController:
    """通用 PID 控制器"""
    def __init__(self, kp, ki, kd, target):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.target = target
        self.integral = 0.0
        self.prev_error = 0.0
        self.deriv_filtered = 0.0
        self.alpha = DERIV_ALPHA
        self.i_limit = I_LIMIT

    def update(self, current, dt):
        error = self.target - current
        p = self.kp * error
        self.integral += error * dt
        if self.integral > self.i_limit:
            self.integral = self.i_limit
        if self.integral < -self.i_limit:
            self.integral = -self.i_limit
        i = self.ki * self.integral
        deriv_raw = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.deriv_filtered = self.alpha * deriv_raw + (1.0 - self.alpha) * self.deriv_filtered
        self.prev_error = error
        d = self.kd * self.deriv_filtered
        output = p + i + d
        return max(0.0, min(1.0, output))  # 0-1 标幺值


class PeltierAuto:
    """v3.2 帕尔贴自动控制 (死区 hysteresis)"""
    def __init__(self):
        self.on = False
        self.auto_mode = True

    def update(self, current):
        if not self.auto_mode:
            return self.on
        if current > PELTIER_ON:
            self.on = True
        elif current < PELTIER_OFF:
            self.on = False
        return self.on


def simulate(use_peltier, label):
    """跑一次模拟, 返回 (time_series, T_series, output_series, peltier_series)"""
    pid = PIDController(KP, KI, KD, TARGET)
    peltier = PeltierAuto() if use_peltier else None

    T = T_AMB
    records = []

    for t in range(int(T_TOTAL_S / SAMPLE_S)):
        output = pid.update(T, SAMPLE_S)
        p_heater = output * P_HEATER_MAX

        peltier_on = peltier.update(T) if peltier else False
        p_peltier = P_PELTIER if peltier_on else 0.0

        dT = (p_heater - H_LOSS * (T - T_AMB) - p_peltier) / C_WATER * SAMPLE_S
        T += dT

        records.append({
            't_s': t * SAMPLE_S,
            'T_actual': round(T, 3),
            'T_target': TARGET,
            'pid_output': round(output, 4),
            'p_heater_w': round(p_heater, 2),
            'p_peltier_w': round(p_peltier, 2),
            'peltier_on': int(peltier_on),
            'peltier_auto': 1 if (peltier and peltier.auto_mode) else 0,
        })

    return records


def save_csv(records, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    return path


def metrics(records, label):
    overshoot = max(r['T_actual'] for r in records) - TARGET
    final_T = records[-1]['T_actual']
    final_err = abs(final_T - TARGET)
    stable_time = None
    for r in records:
        if abs(r['T_actual'] - TARGET) <= 0.3:
            stable_time = r['t_s']
            break
    peltier_on_count = sum(r['peltier_on'] for r in records)
    print('\n=== {0} ==='.format(label))
    print('  最大过冲: {0:+.2f} °C'.format(overshoot))
    print('  最终温度: {0:.2f} °C (target={1})'.format(final_T, TARGET))
    print('  最终误差: {0:.2f} °C'.format(final_err))
    print('  稳态时间 (+/-0.3°C): {0} s'.format(stable_time if stable_time else "未达到"))
    if any(r['peltier_on'] for r in records):
        print('  帕尔贴开启秒数: {0} s ({1:.1f} min)'.format(peltier_on_count, peltier_on_count / 60))
    return {
        'label': label,
        'overshoot': overshoot,
        'final_err': final_err,
        'stable_time': stable_time,
        'peltier_on_s': peltier_on_count,
    }


def plot_compare_matplotlib(records_v31, records_v32, path):
    """matplotlib 双图: 温度对比 + 帕尔贴状态"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    t31 = [r['t_s'] / 60.0 for r in records_v31]
    T31 = [r['T_actual'] for r in records_v31]
    t32 = [r['t_s'] / 60.0 for r in records_v32]
    T32 = [r['T_actual'] for r in records_v32]
    peltier_state = [r['peltier_on'] for r in records_v32]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                                     gridspec_kw={'height_ratios': [3, 1]})

    # 上图: 温度对比
    ax1.plot(t31, T31, 'b-', linewidth=1.5, label='v3.1 (no peltier)', alpha=0.85)
    ax1.plot(t32, T32, 'r-', linewidth=1.5, label='v3.2 (peltier auto)', alpha=0.85)
    ax1.axhline(TARGET, color='g', linestyle='--', linewidth=1, label='target={0}C'.format(TARGET))
    ax1.axhline(PELTIER_ON, color='orange', linestyle=':', linewidth=0.8,
                label='peltier ON={0}C'.format(PELTIER_ON))
    ax1.axhline(PELTIER_OFF, color='orange', linestyle=':', linewidth=0.8,
                label='peltier OFF={0}C'.format(PELTIER_OFF))
    ax1.fill_between([0, 30], PELTIER_OFF, PELTIER_ON, color='orange', alpha=0.08, label='dead zone')
    ax1.set_ylabel('Temperature (C)')
    ax1.set_ylim(30, 40)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.set_title('BrewXOS PID v3.1 vs v3.2 dual-temp 30-min simulation (2026-9-3)')
    ax1.grid(True, alpha=0.3)

    # 下图: v3.2 帕尔贴开关状态
    ax2.fill_between(t32, 0, peltier_state, color='cyan', alpha=0.5, label='peltier ON')
    ax2.set_xlabel('Time (min)')
    ax2.set_ylabel('Peltier')
    ax2.set_ylim(-0.1, 1.3)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(['OFF', 'ON'])
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    png_path = path.replace('.txt', '.png')
    plt.savefig(png_path, dpi=120, bbox_inches='tight')
    plt.close()
    return png_path


def plot_compare_ascii(records_v31, records_v32, path):
    """ASCII fallback, 不覆盖"""
    width = 60
    height = 25
    T_MIN, T_MAX = 30.0, 40.0
    t_total = T_TOTAL_S
    grid = [[' '] * width for _ in range(height)]

    for r in records_v31:
        c = int(r['t_s'] / t_total * (width - 1))
        row = int((T_MAX - r['T_actual']) / (T_MAX - T_MIN) * (height - 1))
        if 0 <= c < width and 0 <= row < height:
            if grid[row][c] == ' ':
                grid[row][c] = '.'

    for r in records_v32:
        c = int(r['t_s'] / t_total * (width - 1))
        row = int((T_MAX - r['T_actual']) / (T_MAX - T_MIN) * (height - 1))
        if 0 <= c < width and 0 <= row < height:
            if grid[row][c] == ' ':
                grid[row][c] = '*'
            elif grid[row][c] == '.':
                grid[row][c] = 'X'

    lines = []
    lines.append('BrewXOS PID v3.1 (.) vs v3.2 (*) 30-min sim  (Y: 30-40 C)')
    lines.append('-' * (width + 12))
    for i, row in enumerate(grid):
        temp = T_MAX - i * (T_MAX - T_MIN) / (height - 1)
        lines.append('{0:5.1f}C |'.format(temp) + ''.join(row) + '|')
    lines.append(' ' * 6 + '+' + '-' * width + '+')
    lines.append(' ' * 7 + '0min' + ' ' * (width - 8) + '30min')
    lines.append('')
    lines.append('Legend: . = v3.1,  * = v3.2,  X = overlap')

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return path


def plot_compare(records_v31, records_v32, path):
    try:
        import matplotlib
        return plot_compare_matplotlib(records_v31, records_v32, path)
    except ImportError:
        return plot_compare_ascii(records_v31, records_v32, path)


if __name__ == '__main__':
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)

    print('=' * 60)
    print('BrewXOS PID v3.1 vs v3.2 simulator (date={0})'.format(date_str))
    print('=' * 60)
    print('Physics: C={0} J/C, h={1} W/C, T_amb={2}C'.format(C_WATER, H_LOSS, T_AMB))
    print('PID: Kp={0}, Ki={1}, Kd={2}, target={3}C, dt={4}s'.format(KP, KI, KD, TARGET, SAMPLE_S))
    print('Peltier: threshold {0}-{1} C, P_peltier={2}W'.format(PELTIER_OFF, PELTIER_ON, P_PELTIER))
    print('Duration: {0}s = {1} min'.format(T_TOTAL_S, T_TOTAL_S / 60))

    print('\n>>> Run v3.1 (no peltier) ...')
    rec_v31 = simulate(use_peltier=False, label='v3.1')
    print('>>> Run v3.2 (peltier auto) ...')
    rec_v32 = simulate(use_peltier=True, label='v3.2')

    p31 = save_csv(rec_v31, os.path.join(data_dir, 'sim_v3_1_{0}.csv'.format(date_str)))
    p32 = save_csv(rec_v32, os.path.join(data_dir, 'sim_v3_2_{0}.csv'.format(date_str)))
    print('\nCSV: {0}\n     {1}'.format(p31, p32))

    m31 = metrics(rec_v31, 'v3.1 (no peltier)')
    m32 = metrics(rec_v32, 'v3.2 (peltier auto)')

    print('\n=== Compare ===')
    if m31['overshoot'] > 0:
        pct = (1 - m32['overshoot'] / m31['overshoot']) * 100
    else:
        pct = 0
    print('  Overshoot reduced: {0:+.2f} C ({1:.0f}%)'.format(
        m31['overshoot'] - m32['overshoot'], pct))
    print('  Final error: v3.1={0:.2f}C, v3.2={1:.2f}C'.format(m31['final_err'], m32['final_err']))
    if m31['stable_time'] and m32['stable_time']:
        print('  Settling time: v3.1={0}s, v3.2={1}s'.format(m31['stable_time'], m32['stable_time']))
    print('  Peltier ON time (v3.2): {0}s = {1:.1f} min'.format(
        m32['peltier_on_s'], m32['peltier_on_s'] / 60))

    plot_path = os.path.join(data_dir, 'sim_compare_{0}.txt'.format(date_str))
    out = plot_compare(rec_v31, rec_v32, plot_path)
    print('\nPlot: {0}'.format(out))
