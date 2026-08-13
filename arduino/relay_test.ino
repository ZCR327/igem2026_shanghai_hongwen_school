/*!
 * MindPlus + 继电器版
 * DFRobot, Mega2560
 *
 * BrewXOS 继电器 bang-bang 测试 v1
 *   - 保留 Mind+ 触控屏（Serial1 9600，5 传感器 n0-n4）
 *   - 加热控制改成继电器（ON/OFF + 0.5°C 滞回）
 *   - 等 MOSFET 到了直接换回 PID v3.1
 *
 * 接线：
 *   继电器 VCC → 5V
 *   继电器 GND → GND
 *   继电器 SIG → D9
 *   12V 电源 + → 继电器 COM
 *   12V 电源 - → 加热膜 -
 *   加热膜 +   → 继电器 NO
 */
#include <DFString.h>
#include <DFRobot_PH.h>
#include <DFRobot_SCD4X.h>
#include <DFRobot_DS18B20.h>
#include <DFRobot_OxygenSensor.h>

#define RELAY_PIN      9
#define READ_MS        1000UL
#define TARGET         35.0
#define HYST           0.5      // 滞回带 35.0 开 / 35.5 关
#define RELAY_ON       HIGH
#define RELAY_OFF      LOW

// 动态变量
String         mind_s_Serial_data, mind_s_total_data, mind_s_fix_data1;
volatile float mind_n_times, mind_n_temp, mind_n_new_target, mind_n_time_control_time,
               mind_n_data;

// 继电器状态
bool relayState = false;
unsigned long startTime;

DFRobot_DS18B20 ds18b20_47;
DFRobot_PH2 ph2;
DFRobot_SCD4X SCD4X(&Wire, 0x62);
DFRobot_OxygenSensor Oxygen;

void DF_end_data();
void DF_mega2560_Reading_environmental_sensor_data(float mind_n_time);
void DF_stir_stick_control(String mind_s_string);
void DF_fix_data();
void DF_setup();
void DF_relay_output();

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
  DF_relay_output();                              // 继电器 bang-bang（每秒）
  if ((Serial1.available())) {
    mind_s_Serial_data = (String(char(Serial1.read())));
    DF_stir_stick_control(mind_s_Serial_data);
    DF_fix_data();
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
  if ((mind_s_string=="a")) digitalWrite(41, HIGH);
  if ((mind_s_string=="b")) digitalWrite(41, LOW);
  if ((mind_s_string=="c")) { digitalWrite(42, HIGH); }
  if ((mind_s_string=="d")) digitalWrite(42, LOW);
  if ((mind_s_string=="g")) { digitalWrite(43, HIGH); }
  if ((mind_s_string=="h")) digitalWrite(43, LOW);
}

void DF_fix_data() {
  if ((mind_s_Serial_data=="t")) {
    mind_s_total_data = "t";
    for (int index = 0; index < 5; index++) {
      delay(100);
      mind_s_fix_data1 = (String(char(Serial1.read())));
      mind_s_total_data = (String(mind_s_total_data) + String(mind_s_fix_data1));
      yield();
    }
  }
}

void DF_relay_output() {
  static unsigned long tLast = 0;
  unsigned long now = millis();
  if (now - tLast < READ_MS) return;
  float dt = (now - tLast) / 1000.0f;
  tLast = now;
  if (dt <= 0 || dt > 5.0) dt = 1.0;

  // 用 DFRobot_DS18B20 对象读温度（避免与标准库冲突）
  float current = ds18b20_47.getTempC();

  if (current == -127.0 || current == 85.0) {
    Serial.println(F("TEMP_SENSOR_ERROR -> relay OFF"));
    digitalWrite(RELAY_PIN, RELAY_OFF);
    relayState = false;
    delay(1000);
    return;
  }

  // bang-bang 控制 + 滞回
  if (!relayState && current < TARGET - HYST) {
    digitalWrite(RELAY_PIN, RELAY_ON);
    relayState = true;
  } else if (relayState && current > TARGET + HYST) {
    digitalWrite(RELAY_PIN, RELAY_OFF);
    relayState = false;
  }

  // USB 串口打印（115200）
  float error = TARGET - current;
  Serial.print(F("T="));      Serial.print(current, 2);
  Serial.print(F(" err="));   Serial.print(error, 2);
  Serial.print(F("  Relay=")); Serial.println(relayState ? "ON" : "OFF");
}

void DF_setup() {
  Serial1.begin(9600);          // 锁死！触控屏硬件 9600
  Serial.begin(115200);         // USB 调试
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF);
  startTime = millis();
  mind_n_time_control_time = 0;
  mind_n_new_target = 0;
  mind_n_times = 0;
  mind_n_data = 0;
  mind_s_Serial_data = "";
  Serial.println(F("===== BrewXOS Relay Bang-Bang v1 ====="));
  Serial.print(F("Target=")); Serial.print(TARGET);
  Serial.print(F("  Hyst=+-")); Serial.println(HYST);
}
