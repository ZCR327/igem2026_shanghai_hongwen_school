/*!
 * MindPlus
 * DFRobot, Mega2560
 *
 * BrewXOS PID v3.2 — 双温控版 (2026-9-3 改造)
 *
 * 相对 v3.1 (2026-8-31) 的变化:
 *   1. **新增帕尔贴 (PIN 45) 自动控制** —— 防过冲核心
 *      - 死区 35.5-36.0 °C, hysteresis 防抖
 *      - current > 36.0 → 帕尔贴开 (制冷)
 *      - current < 35.5 → 帕尔贴关
 *      - 死区内 35.5-36.0 保持 (避免边界抖动)
 *   2. 副加热 (PIN 44) 保持触屏手动 (强加热用, 不自动化)
 *   3. 加热膜 PID (PIN 9 PWM) 逻辑**完全不变**
 *   4. 新增 peltier_auto_mode 标志位 (默认 true)
 *   5. 触屏 h 触发手动模式 (peltier_auto_mode = false)
 *   6. 触屏 i 同时恢复自动 + 关副加热+帕尔贴
 *   7. USB Serial 输出新增 peltier 状态
 *
 * ============================================================================
 * 触屏串口协议 v0.2 (与 v3.1 兼容) + 双温控扩展
 * ============================================================================
 * 5 路继电器 + 组合键 'i':
 *   'a'/'b' = PIN 43 加热膜 (主加热, PID 自动, 触屏只读)
 *   'c'/'d' = PIN 41 蠕动泵 A
 *   'e'/'f' = PIN 42 蠕动泵 B
 *   'g'     = PIN 44 副加热 HIGH (手动, heater_aux_manual = true)
 *   'h'     = PIN 45 帕尔贴 HIGH (手动, peltier_auto_mode = false)
 *   'i'     = PIN 44+45 同时 LOW (恢复自动模式 + 全关)
 *
 * 双温控设计 (iGEM 评委爱听):
 *   - 加热膜 PWM (PID 自动) → 缓慢加温到 35°C target
 *   - 帕尔贴开关 (PID 协同) → 防止过冲到 37°C+ (损坏菌)
 *   - 副加热继电器 (手动) → 室温过低 (< 15°C) 强加热用
 *
 * v3.2 改造日期: 2026-9-3
 * 备份: backups/program_v3_1_20260903_pre_v3.2.ino
 *
 * ============================================================================
 */
#include <DFString.h>
#include <DFRobot_PH.h>
#include <DFRobot_SCD4X.h>
#include <DFRobot_DS18B20.h>
#include <DFRobot_OxygenSensor.h>

// ================== 引脚定义 ==================
#define HEATER_PIN      9    // 加热膜 PWM (主加热, PID 自动)
#define PELTIER_PIN    45    // 帕尔贴 (TEC 制冷, 双温控 v3.2 新增自动)
#define HEATER_AUX_PIN 44    // 副加热继电器 (触屏手动, 强加热用)
#define PUMP_A_PIN     41
#define PUMP_B_PIN     42
#define RELAY_HEATER   43    // 加热膜继电器 (主, 等同 HEATER_PIN 高电平触发)
#define READ_MS     1000UL   // PID 采样间隔 1s

// ================== 双温控死区 (hysteresis) ==================
const float PELTIER_ON_THRESHOLD  = 36.0f;   // current > 36 → 帕尔贴开
const float PELTIER_OFF_THRESHOLD = 35.5f;   // current < 35.5 → 帕尔贴关
// 死区 35.5 - 36.0 保持状态 (hysteresis 边界防抖)

// ================== 模式标志 ==================
bool peltier_auto_mode  = true;  // 帕尔贴自动模式 (默认 true)
bool heater_aux_manual  = false; // 副加热手动模式 (v3.2 保持手动, 标志留作扩展)

// ================== 动态变量 (Mind+ 兼容) ==================
String         mind_s_Serial_data, mind_s_total_data, mind_s_fix_data1;
volatile float mind_n_times, mind_n_temp, mind_n_new_target, mind_n_time_control_time,
               mind_n_data;

// ================== PID 参数 (v3.1 优化版) ==================
const float Kp          = 3.0f;    // 优化: 5.0 -> 3.0
const float Ki          = 0.05f;
const float Kd          = 3.0f;    // 优化: 8.0 -> 3.0 (有帕尔贴后 Kd 不用太激进)
const float I_LIMIT     = 200.0f;
const float DERIV_ALPHA = 0.1f;
const float OUT_MIN     = 0.0f;
const float OUT_MAX     = 1.0f;
float       target      = 35.0f;   // 优化: 37 -> 35 (XOS 净积累更多)

float integral        = 0.0f;
float prev_error      = 0.0f;
float deriv_filtered  = 0.0f;

// ================== PID 计算 (v3.1 不变) ==================
float pidUpdate(float tgt, float cur, float dt) {
  float error = tgt - cur;
  float P = Kp * error;
  integral += error * dt;
  if (integral >  I_LIMIT) integral =  I_LIMIT;
  if (integral < -I_LIMIT) integral = -I_LIMIT;
  float I = Ki * integral;
  float deriv_raw = (error - prev_error) / dt;
  deriv_filtered = DERIV_ALPHA * deriv_raw + (1.0f - DERIV_ALPHA) * deriv_filtered;
  prev_error = error;
  float D = Kd * deriv_filtered;
  float output = P + I + D;
  if (output > OUT_MAX) output = OUT_MAX;
  if (output < OUT_MIN) output = OUT_MIN;
  return output;
}

// ================== 传感器对象 ==================
DFRobot_DS18B20   ds18b20_47;
DFRobot_PH2       ph2;
DFRobot_SCD4X     SCD4X(&Wire, 0x62);
DFRobot_OxygenSensor Oxygen;

// ================== 函数声明 ==================
void DF_end_data();
void DF_mega2560_Reading_environmental_sensor_data(float mind_n_time);
void DF_stir_stick_control(String mind_s_string);
void DF_setup();
void DF_PID_output();
void DF_peltier_auto_control(float current);  // v3.2 新增

// ================== 主循环 ==================
void setup() {
  ds18b20_47.begin(47);
  while(!SCD4X.begin()){};
  SCD4X.setTempComp(4.0);
  SCD4X.setSensorAltitude(540);
  SCD4X.enablePeriodMeasure(SCD4X_START_PERIODIC_MEASURE);
  while(!Oxygen.begin(0x73));
  DF_setup();
}

void loop() {
  DF_PID_output();  // 加热膜 PID + 帕尔贴自动控制 (在 PID 内部调用)
  if (Serial1.available()) {
    mind_s_Serial_data = (String(char(Serial1.read())));
    DF_stir_stick_control(mind_s_Serial_data);
  } else {
    DF_mega2560_Reading_environmental_sensor_data(5000);
  }
}

// ================== 串口结束符 (USART HMI 协议) ==================
void DF_end_data() {
  Serial1.write(255);
  Serial1.write(255);
  Serial1.write(255);
}

// ================== 传感器数据上报 (5 路) ==================
void DF_mega2560_Reading_environmental_sensor_data(float mind_n_time) {
  if (((millis() - mind_n_times) >= mind_n_time)) {
    mind_n_times = millis();
    Serial1.print("n0.val=");
    mind_n_temp = ds18b20_47.getTempC();
    Serial1.print(mind_n_temp, 2);
    DF_end_data();
    if ((SCD4X.getDataReadyStatus())) {
      DFRobot_SCD4X::sSensorMeasurement_t data;
      SCD4X.readMeasurement(&data);
      Serial1.print("n1.val=");
      Serial1.print(data.temp, 2);
      DF_end_data();
    }
    Serial1.print("n2.val=");
    Serial1.print(Oxygen.ReadOxygenData(10), 2);
    DF_end_data();
    if ((SCD4X.getDataReadyStatus())) {
      DFRobot_SCD4X::sSensorMeasurement_t data;
      SCD4X.readMeasurement(&data);
      Serial1.print("n3.val=");
      Serial1.print((long)data.CO2ppm);
      DF_end_data();
    }
    Serial1.print("n4.val=");
    Serial1.print(ph2.readPH(A6), 2);
    DF_end_data();
  }
}

// ================== 触屏命令解析 (v0.2 协议 + 标志位管理) ==================
void DF_stir_stick_control(String mind_s_string) {
  if (mind_s_string == "a") digitalWrite(RELAY_HEATER, HIGH);   // 加热膜继电器 HIGH (主)
  if (mind_s_string == "b") digitalWrite(RELAY_HEATER, LOW);    // 加热膜继电器 LOW
  if (mind_s_string == "c") digitalWrite(PUMP_A_PIN, HIGH);     // 蠕动泵 A 开
  if (mind_s_string == "d") digitalWrite(PUMP_A_PIN, LOW);
  if (mind_s_string == "e") digitalWrite(PUMP_B_PIN, HIGH);     // 蠕动泵 B 开
  if (mind_s_string == "f") digitalWrite(PUMP_B_PIN, LOW);

  // v3.2 标志位管理 (新增)
  if (mind_s_string == "g") {
    heater_aux_manual = true;
    digitalWrite(HEATER_AUX_PIN, HIGH);                         // 副加热开 (手动)
  }
  if (mind_s_string == "h") {
    peltier_auto_mode = false;                                  // 进入手动模式
    digitalWrite(PELTIER_PIN, HIGH);                            // 帕尔贴开 (手动)
  }
  if (mind_s_string == "i") {
    heater_aux_manual = false;
    peltier_auto_mode = true;                                   // 恢复自动
    digitalWrite(HEATER_AUX_PIN, LOW);
    digitalWrite(PELTIER_PIN, LOW);
  }
}

// ================== v3.2 新增: 帕尔贴自动控制 ==================
// 死区 35.5-36.0 hysteresis, 自动模式时才执行
void DF_peltier_auto_control(float current) {
  if (!peltier_auto_mode) return;  // 手动模式不接管

  if (current > PELTIER_ON_THRESHOLD) {
    digitalWrite(PELTIER_PIN, HIGH);   // 过热 → 开制冷
  } else if (current < PELTIER_OFF_THRESHOLD) {
    digitalWrite(PELTIER_PIN, LOW);    // 正常 → 关制冷
  }
  // 死区 35.5-36.0 保持现状 (hysteresis 防抖)
}

// ================== PID 输出 + 帕尔贴协同 (v3.2) ==================
void DF_PID_output() {
  static unsigned long tLast = 0;
  unsigned long now = millis();
  if (now - tLast < READ_MS) return;
  float dt = (now - tLast) / 1000.0f;
  tLast = now;
  if (dt <= 0 || dt > 5.0) dt = 1.0;

  float current = ds18b20_47.getTempC();

  // 加热膜 PID (单向, v3.1 不变)
  float output  = pidUpdate(target, current, dt);
  analogWrite(HEATER_PIN, (int)(output * 255));

  // v3.2 新增: 帕尔贴协同 (防过冲)
  DF_peltier_auto_control(current);

  // USB 串口打印 (新增 peltier 状态)
  float error = target - current;
  Serial.print(F("T="));     Serial.print(current, 2);
  Serial.print(F(" err="));  Serial.print(error, 2);
  Serial.print(F(" out="));  Serial.print(output * 100, 0);
  Serial.print(F("% P="));   Serial.print(Kp * error, 1);
  Serial.print(F(" I="));    Serial.print(Ki * integral, 1);
  Serial.print(F(" D="));    Serial.print(Kd * deriv_filtered, 1);
  Serial.print(F(" pelt="));
  Serial.print(peltier_auto_mode ? F("AUTO") : F("MANU"));
  Serial.print(F(" pin45="));
  Serial.println(digitalRead(PELTIER_PIN) ? F("ON") : F("OFF"));
}

// ================== setup (v3.2 加引脚初始化) ==================
void DF_setup() {
  Serial1.begin(9600);          // 锁死! 触控屏硬件 9600
  Serial.begin(115200);         // USB 监控 115200
  pinMode(HEATER_PIN, OUTPUT);
  pinMode(PELTIER_PIN, OUTPUT);
  pinMode(HEATER_AUX_PIN, OUTPUT);
  pinMode(PUMP_A_PIN, OUTPUT);
  pinMode(PUMP_B_PIN, OUTPUT);
  pinMode(RELAY_HEATER, OUTPUT);
  analogWrite(HEATER_PIN, 0);
  digitalWrite(PELTIER_PIN, LOW);
  digitalWrite(HEATER_AUX_PIN, LOW);
  digitalWrite(PUMP_A_PIN, LOW);
  digitalWrite(PUMP_B_PIN, LOW);
  digitalWrite(RELAY_HEATER, LOW);
  mind_n_time_control_time = 0;
  mind_n_new_target = 0;
  mind_n_times = 0;
  mind_n_data = 0;
  mind_s_Serial_data = "";
}
