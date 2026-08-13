/*!
 * BrewXOS PID Auto-Tuning via Relay Feedback Method
 * (Astrom-Haggland / Ziegler-Nichols ultimate gain)
 *
 * DFRobot Mega2560
 *
 * 3 阶段:
 *   1. WARMUP       - 继电器 bang-bang 升温到 setpoint
 *   2. OSCILLATION  - 检测自激振荡，量 Tu 和 A
 *   3. CALCULATE    - 套 Z-N 公式输出 Kp/Ki/Kd
 *
 * 接线:
 *   继电器 SIG  -> D9
 *   DS18B20 DATA -> D2 (4.7kΩ 上拉到 5V)
 *   12V 电源 + -> 继电器 COM
 *   加热膜 +   -> 继电器 NO
 *   12V 电源 - -> 加热膜 -
 */
#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS    2
#define RELAY_PIN       9
#define TARGET          35.0
#define HYST            0.5
#define SETTLE_CYCLES   3       // 跳过前 3 个不稳定周期
#define SAMPLE_MS       500    // 0.5s 采样

// 状态机
enum State { WARMUP, OSCILLATION, CALCULATE, DONE, PID_TEST };
State state = WARMUP;

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// 振荡数据
float cycle_max[10];     // 每个周期的最高温
float cycle_min[10];     // 每个周期的最低温
unsigned long cycle_start[10];
unsigned long cycle_end[10];
int cycle_count = 0;
int current_cycle_max_idx = 0;
bool relay_state = false;
float current_max = -100;
float current_min = 200;

unsigned long start_time;
unsigned long t_relay_change = 0;

// 算出的 PID 参数
float Kp_zn = 0, Ki_zn = 0, Kd_zn = 0;
float Tu = 0, A_amp = 0, Ku = 0;

void setup() {
  Serial.begin(115200);
  sensors.begin();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  start_time = millis();

  Serial.println(F("===== BrewXOS Auto-Tune (Relay Feedback) ====="));
  Serial.print(F("Setpoint: ")); Serial.print(TARGET); Serial.print(F(" C"));
  Serial.print(F("  Hyst: +-")); Serial.println(HYST);
  Serial.println();
  Serial.println(F("Phase 1: WARMUP - heat to setpoint..."));
}

float read_temp() {
  sensors.requestTemperatures();
  float t = sensors.getTempCByIndex(0);
  if (t == -127.0 || t == 85.0) return -127.0;
  return t;
}

void update_relay(float T) {
  if (T == -127.0) {
    digitalWrite(RELAY_PIN, LOW);
    return;
  }
  if (!relay_state && T < TARGET - HYST) {
    digitalWrite(RELAY_PIN, HIGH);
    relay_state = true;
    t_relay_change = millis();
  } else if (relay_state && T > TARGET + HYST) {
    digitalWrite(RELAY_PIN, LOW);
    relay_state = false;
    t_relay_change = millis();
  }
}

void record_cycle() {
  if (cycle_count >= 10) return;
  unsigned long now = millis();
  if (relay_state) {
    // 刚转为 ON，开始新周期
    cycle_start[cycle_count] = t_relay_change;
    cycle_min[cycle_count] = current_min;
    current_min = 200;
    current_max = -100;
  } else {
    // 刚转为 OFF，结束当前周期
    if (cycle_count > 0 || current_min < 200) {
      cycle_end[cycle_count] = t_relay_change;
      cycle_max[cycle_count] = current_max;
      cycle_count++;
    }
  }
}

void calculate_zn() {
  if (cycle_count <= SETTLE_CYCLES) return;

  int valid = cycle_count - SETTLE_CYCLES;
  float sum_period = 0, sum_amp = 0;
  for (int i = SETTLE_CYCLES; i < cycle_count; i++) {
    float period = (cycle_end[i] - cycle_start[i]) / 1000.0;
    float amp = cycle_max[i] - cycle_min[i];
    sum_period += period;
    sum_amp += amp;
  }
  Tu = sum_period / valid;        // 秒
  A_amp = sum_amp / valid;        // °C

  // Z-N 终极增益公式
  // d = 继电器滞回 = 2 * HYST (继电器从 OFF 到 ON 的跳变量)
  float d = 2.0 * HYST;
  Ku = 4.0 * d / (3.14159 * A_amp);

  // Z-N PID 参数
  Kp_zn = 0.6 * Ku;
  float Ti = 0.5 * Tu;             // 积分时间 (秒)
  float Td = 0.125 * Tu;           // 微分时间 (秒)
  Ki_zn = Kp_zn / Ti;
  Kd_zn = Kp_zn * Td;

  state = CALCULATE;
}

void print_results() {
  Serial.println();
  Serial.println(F("=================================================="));
  Serial.println(F("Phase 3: Ziegler-Nichols Auto-Tune RESULTS"));
  Serial.println(F("=================================================="));
  Serial.print(F("Oscillation period Tu = ")); Serial.print(Tu, 2); Serial.println(F(" s"));
  Serial.print(F("Oscillation amplitude A = ")); Serial.print(A_amp, 3); Serial.println(F(" C"));
  Serial.print(F("Ultimate gain Ku = ")); Serial.print(Ku, 3)); Serial.println();
  Serial.println();
  Serial.println(F("--- Z-N PID Parameters ---"));
  Serial.print(F("  Kp = ")); Serial.println(Kp_zn, 3);
  Serial.print(F("  Ki = ")); Serial.println(Ki_zn, 4);
  Serial.print(F("  Kd = ")); Serial.println(Kd_zn, 3);
  Serial.println();
  Serial.println(F("--- Tyreus-Luyben (conservative, better for temp) ---"));
  Serial.print(F("  Kp = ")); Serial.println(Ku * 0.45, 3);
  Serial.print(F("  Ki = ")); Serial.println(Ku * 0.45 / (2.2 * Tu), 4);
  Serial.print(F("  Kd = ")); Serial.println(Ku * 0.45 * Tu / 6.3, 3);
  Serial.println();
  Serial.println(F("--- IMC (very conservative) ---"));
  Serial.print(F("  Kp = ")); Serial.println(Ku * 0.4, 3);
  Serial.print(F("  Ki = ")); Serial.println(Ku * 0.4 / Tu, 4);
  Serial.print(F("  Kd = ")); Serial.println(Ku * 0.4 * Tu / 3, 3));
  Serial.println();
  Serial.println(F("Copy these to program_v3_1.ino"));
  Serial.println(F("Kp = 3.0, Ki = 0.05, Kd = 3.0  --  to  --  Kp = ?, Ki = ?, Kd = ?"));
}

void run_pid_test(float Kp, float Ki, float Kd, float T_set, unsigned long duration_ms) {
  // 简单 PID 实现测试
  float integral = 0, prev_err = 0;
  unsigned long t_start = millis();
  unsigned long t_last = t_start;
  Serial.println();
  Serial.println(F("=== PID TEST (using new K) ==="));
  Serial.print(F("Kp=")); Serial.print(Kp);
  Serial.print(F(" Ki=")); Serial.print(Ki);
  Serial.print(F(" Kd=")); Serial.print(Kd);
  Serial.print(F(" Target=")); Serial.println(T_set);

  while (millis() - t_start < duration_ms) {
    sensors.requestTemperatures();
    float T = sensors.getTempCByIndex(0);
    unsigned long now = millis();
    float dt = (now - t_last) / 1000.0;
    if (dt <= 0 || dt > 5.0) dt = 1.0;
    t_last = now;

    if (T == -127.0) {
      Serial.println(F("TEMP_ERROR"));
      digitalWrite(RELAY_PIN, LOW);
      delay(500);
      continue;
    }

    float err = T_set - T;
    integral += err * dt;
    if (integral > 100) integral = 100;
    if (integral < -100) integral = -100;
    float deriv = (err - prev_err) / dt;
    prev_err = err;

    float output = Kp * err + Ki * integral + Kd * deriv;
    output = constrain(output, 0, 1);

    // PWM via relay: 大于 0.5 开，小于 0.5 关
    bool new_state = output > 0.5;
    if (new_state != relay_state) {
      digitalWrite(RELAY_PIN, new_state ? HIGH : LOW);
      relay_state = new_state;
    }

    Serial.print(F("T=")); Serial.print(T, 2);
    Serial.print(F(" err=")); Serial.print(err, 2);
    Serial.print(F(" out=")); Serial.print(output * 100, 0);
    Serial.print(F("% Relay=")); Serial.println(relay_state ? "ON" : "OFF");

    delay(500);
  }
  digitalWrite(RELAY_PIN, LOW);
  Serial.println(F("=== PID test done ==="));
}

void loop() {
  static unsigned long t_last_sample = 0;
  static unsigned long t_last_print = 0;
  static int last_relay_state = -1;
  unsigned long now = millis();

  if (now - t_last_sample < SAMPLE_MS) return;
  t_last_sample = now;

  float T = read_temp();

  switch (state) {
    case WARMUP:
      update_relay(T);
      // 检测继电器状态变化
      if ((int)relay_state != last_relay_state) {
        last_relay_state = relay_state;
        Serial.print(F("[WARMUP] T=")); Serial.print(T, 2);
        Serial.print(F(" Relay=")); Serial.println(relay_state ? "ON" : "OFF");
      }
      // 转 OSCILLATION 当 cycle 至少 1 个
      if (cycle_count >= 1) {
        state = OSCILLATION;
        Serial.println();
        Serial.println(F("Phase 2: OSCILLATION - measuring cycles..."));
      }
      break;

    case OSCILLATION:
      update_relay(T);
      if (T != -127.0) {
        if (T > current_max) current_max = T;
        if (T < current_min) current_min = T;
      }
      // 检测继电器状态变化
      if ((int)relay_state != last_relay_state) {
        record_cycle();
        last_relay_state = relay_state;
        Serial.print(F("[OSC ")); Serial.print(cycle_count);
        Serial.print(F("] t=")); Serial.print((now - start_time) / 1000.0, 1);
        Serial.print(F("s  T=")); Serial.print(T, 2);
        Serial.print(F("  Relay=")); Serial.println(relay_state ? "ON" : "OFF");

        if (cycle_count >= SETTLE_CYCLES + 3) {
          calculate_zn();
          print_results();
          state = DONE;
        }
      }
      break;

    case CALCULATE:
      // 计算中（已自动跳到 DONE）
      break;

    case DONE:
      // 等待用户输入
      if (Serial.available()) {
        char c = Serial.read();
        if (c == 'p' || c == 'P') {
          // 用 Z-N Kp 测试 PID
          state = PID_TEST;
          run_pid_test(Kp_zn, Ki_zn, Kd_zn, TARGET, 120000);  // 2 min 测试
          state = DONE;
        }
        if (c == 't' || c == 'T') {
          // 用 Tyreus-Luyben 测试
          float Kp_tl = Ku * 0.45;
          float Ki_tl = Kp_tl / (2.2 * Tu);
          float Kd_tl = Kp_tl * Tu / 6.3;
          state = PID_TEST;
          run_pid_test(Kp_tl, Ki_tl, Kd_tl, TARGET, 120000);
          state = DONE;
        }
        if (c == 'r' || c == 'R') {
          // 重置重新调
          state = WARMUP;
          cycle_count = 0;
          current_max = -100;
          current_min = 200;
          Serial.println(F("Reset - restarting WARMUP..."));
        }
      }
      // 每 5s 提醒一次可以输入
      if (now - t_last_print > 5000) {
        t_last_print = now;
        Serial.println(F("Type 'p' to test Z-N K, 't' to test T-L K, 'r' to reset"));
      }
      break;

    case PID_TEST:
      // 跑测试中（run_pid_test 内部循环）
      break;
  }
}
