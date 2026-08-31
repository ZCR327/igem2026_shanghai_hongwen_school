/*!
 * MindPlus
 * DFRobot, Mega2560
 *
 * BrewXOS PID v3.1 — 优化版 (2026.8.12, **2026.8.31 同步触屏协议到 v0.2**)
 *
 * 优化来源：差分进化 + 网格搜索（optimize_pid.py）
 *   - Kp: 5.0 → 3.0
 *   - Kd: 8.0 → 3.0（防过冲）
 *   - target: 37 → 35（仿真发现 35°C XOS 净积累多 30-50%）
 *
 * 5 个修复（v3 → v3.1）:
 *   1. target = 35（优化：菌消耗更少）
 *   2. loop() 顶部加 DF_PID_output() 调用
 *   3. 传感器去 toInt() 保留 2 位小数
 *   4. USB Serial 改 115200（Serial1 触控屏 9600 锁死不能动）
 *   5. 加 pinMode(HEATER_PIN, OUTPUT) 保证 PWM 正常
 *
 * ============================================================================
 * 触屏串口协议 v0.2（**当前生效，与 8.31 老师改版一致**）
 * ============================================================================
 * 5 路继电器 + 组合键 'i'（与 Mind+ 8.31 mpcode 完全同步）:
 *   'a' = PIN 43 Open   'b' = PIN 43 Close  ← 加热膜
 *   'c' = PIN 41 Open   'd' = PIN 41 Close  ← 蠕动泵 A
 *   'e' = PIN 42 Open   'f' = PIN 42 Close  ← 蠕动泵 B
 *   'g' = PIN 44 Open                       ← 搅拌电机
 *   'h' = PIN 45 Open                       ← 备用气泵
 *   'i' = PIN 44 + 45 一起关                ← 组合键（一键全停）
 *
 * v0.1 协议（a/b/c/d/g/h/t, 8.12 那版）已废弃，DF_fix_data() 函数已删除。
 *
 * 协议对比表：docs/hardware/serial_protocol_20260831.md
 * Auto-tune 操作手册：docs/hardware/auto_tune_runbook_20260831.md
 * ============================================================================
 */
#include <DFString.h>
#include <DFRobot_PH.h>
#include <DFRobot_SCD4X.h>
#include <DFRobot_DS18B20.h>
#include <DFRobot_OxygenSensor.h>

#define HEATER_PIN   9
#define READ_MS      1000UL

// 动态变量
String         mind_s_Serial_data, mind_s_total_data, mind_s_fix_data1;
volatile float mind_n_times, mind_n_temp, mind_n_new_target, mind_n_time_control_time,
               mind_n_data;

// 创建对象 + PID 参数（v3.1 优化版）
const float Kp          = 3.0;           // 优化: 5.0 -> 3.0
const float Ki          = 0.05;
const float Kd          = 3.0;           // 优化: 8.0 -> 3.0（防过冲）
const float I_LIMIT     = 200.0;
const float DERIV_ALPHA = 0.1;
const float OUT_MIN     = 0.0;
const float OUT_MAX     = 1.0;
float       target      = 35.0;          // 优化: 37 -> 35（XOS 净积累更多）

float integral        = 0.0;
float prev_error      = 0.0;
float deriv_filtered  = 0.0;

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

DFRobot_DS18B20 ds18b20_47;
DFRobot_PH2 ph2;
DFRobot_SCD4X SCD4X(&Wire, 0x62);
DFRobot_OxygenSensor Oxygen;

void DF_end_data();
void DF_mega2560_Reading_environmental_sensor_data(float mind_n_time);
void DF_stir_stick_control(String mind_s_string);
void DF_setup();
void DF_PID_output();

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
  DF_PID_output();
  if ((Serial1.available())) {
    mind_s_Serial_data = (String(char(Serial1.read())));
    DF_stir_stick_control(mind_s_Serial_data);
  }
  else {
    DF_mega2560_Reading_environmental_sensor_data(5000);
  }
}

void DF_end_data() {
  Serial1.write(255);
  Serial1.write(255);
  Serial1.write(255);
}

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

void DF_stir_stick_control(String mind_s_string) {
  if ((mind_s_string=="a")) digitalWrite(43, HIGH);  // 加热膜 开
  if ((mind_s_string=="b")) digitalWrite(43, LOW);   // 加热膜 关
  if ((mind_s_string=="c")) digitalWrite(41, HIGH);  // 蠕动泵 A 开
  if ((mind_s_string=="d")) digitalWrite(41, LOW);   // 蠕动泵 A 关
  if ((mind_s_string=="e")) digitalWrite(42, HIGH);  // 蠕动泵 B 开
  if ((mind_s_string=="f")) digitalWrite(42, LOW);   // 蠕动泵 B 关
  if ((mind_s_string=="g")) digitalWrite(44, HIGH);  // 搅拌电机 开
  if ((mind_s_string=="h")) digitalWrite(45, HIGH);  // 备用气泵 开
  if ((mind_s_string=="i")) {                         // 组合键: 搅拌电机 + 备用气泵 同时关
    digitalWrite(44, LOW);
    digitalWrite(45, LOW);
  }
}

void DF_PID_output() {
  static unsigned long tLast = 0;
  unsigned long now = millis();
  if (now - tLast < READ_MS) return;
  float dt = (now - tLast) / 1000.0f;
  tLast = now;
  if (dt <= 0 || dt > 5.0) dt = 1.0;

  float current = ds18b20_47.getTempC();
  float output  = pidUpdate(target, current, dt);
  analogWrite(HEATER_PIN, (int)(output * 255));

  float error = target - current;
  Serial.print(F("T="));     Serial.print(current, 2);
  Serial.print(F(" err="));  Serial.print(error, 2);
  Serial.print(F(" out="));  Serial.print(output * 100, 0);
  Serial.print(F("% P="));   Serial.print(Kp * error, 1);
  Serial.print(F(" I="));    Serial.print(Ki * integral, 1);
  Serial.print(F(" D="));    Serial.println(Kd * deriv_filtered, 1);
}

void DF_setup() {
  Serial1.begin(9600);          // 锁死！触控屏硬件 9600
  Serial.begin(115200);
  pinMode(HEATER_PIN, OUTPUT);
  analogWrite(HEATER_PIN, 0);
  mind_n_time_control_time = 0;
  mind_n_new_target = 0;
  mind_n_times = 0;
  mind_n_data = 0;
  mind_s_Serial_data = "";
}
