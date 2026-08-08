/*!
 * BrewXOS Sensor Logger - DFRduino Mega2560
 * Author: Thomas ZHAO (赵昶瑞), iGEM 2026
 *
 * Reads 4 sensors (pH, DO, CO2, T) every 5s and prints CSV to Serial.
 * Also logs to SD card if one is attached (CS pin 46).
 * Pin 46 controls heating element (relay module).
 *
 * Test protocol:
 *   Serial Monitor: send '1' to turn heater OFF, '2' to turn heater ON.
 */
#include <DFRobot_PH.h>
#include <DFRobot_SCD4X.h>
#include <DFRobot_DS18B20.h>
#include <DFRobot_OxygenSensor.h>
#include <Wire.h>

// ====== I2C addresses ======
#define O2_I2C_ADDR     0x73
#define SCD4X_I2C_ADDR  0x62

// ====== Pin assignments ======
#define PIN_DS18B20     41     // DS18B20 data line
#define PIN_RELAY       46     // Relay module for heating element
#define PIN_PH_ANALOG   A11    // pH probe analog input

// ====== Configuration ======
#define LOG_INTERVAL_MS  5000   // 5 seconds between readings
#define SCD4X_ALTITUDE_M 540    // Shanghai altitude (m)
#define SCD4X_TEMP_COMP_C 4.0   // Temperature compensation (C)

// ====== Sensor objects ======
DFRobot_OxygenSensor Oxygen;
DFRobot_SCD4X SCD4X(&Wire, SCD4X_I2C_ADDR);
DFRobot_DS18B20 ds18b20;
DFRobot_PH2 ph;

// ====== State ======
unsigned long last_log = 0;
unsigned int  sample_count = 0;
bool          heater_on = false;
unsigned long t_start = 0;

// ====== CSV header (printed once) ======
void printHeader() {
    Serial.println(F("time_s,timestamp_ms,temp_C,pH,DO_pct,CO2_ppm,heater"));
}

// ====== Sample + print one row ======
void sampleAndLog() {
    float t = ds18b20.getTempC();
    float pH = ph.readPH(PIN_PH_ANALOG);
    float o2 = Oxygen.ReadOxygenData(10);   // 10 averaged samples

    float co2 = NAN;
    if (SCD4X.getDataReadyStatus()) {
        DFRobot_SCD4X::sSensorMeasurement_t data;
        SCD4X.readMeasurement(&data);
        co2 = data.CO2ppm;
    }

    unsigned long now = millis();
    float t_s = (now - t_start) / 1000.0;

    Serial.print(t_s, 2);          Serial.print(",");
    Serial.print(now);              Serial.print(",");
    Serial.print(t, 2);             Serial.print(",");
    Serial.print(pH, 2);            Serial.print(",");
    Serial.print(o2, 2);            Serial.print(",");
    Serial.print(co2, 0);           Serial.print(",");
    Serial.println(heater_on ? 1 : 0);

    sample_count++;
}


void setup() {
    Serial.begin(115200);
    while (!Serial) { ; }   // wait for Serial on Leonardo/Micro

    // I2C
    Wire.begin();

    // pH sensor (analog, no init needed)
    // DS18B20 (1-Wire, no init needed)
    ds18b20.begin(PIN_DS18B20);

    // Wait for O2 sensor
    Serial.print(F("Waiting for DO sensor at 0x73..."));
    while (!Oxygen.begin(O2_I2C_ADDR)) {
        Serial.print(F("."));
        delay(500);
    }
    Serial.println(F(" OK"));

    // Wait for SCD4X
    Serial.print(F("Waiting for CO2 sensor at 0x62..."));
    while (!SCD4X.begin()) {
        Serial.print(F("."));
        delay(500);
    }
    Serial.println(F(" OK"));
    SCD4X.setTempComp(SCD4X_TEMP_COMP_C);
    SCD4X.setSensorAltitude(SCD4X_ALTITUDE_M);
    SCD4X.enablePeriodMeasure(SCD4X_START_PERIODIC_MEASURE);

    // Relay pin
    pinMode(PIN_RELAY, OUTPUT);
    digitalWrite(PIN_RELAY, LOW);   // heater off by default

    // CSV header
    printHeader();
    t_start = millis();
    last_log = t_start;
    Serial.println(F("# BrewXOS sensor logger started. Send '1' = heater OFF, '2' = heater ON."));
}


void loop() {
    // Periodic sampling
    unsigned long now = millis();
    if (now - last_log >= LOG_INTERVAL_MS) {
        last_log = now;
        sampleAndLog();
    }

    // Serial command interface
    if (Serial.available() > 0) {
        int cmd = Serial.parseInt();
        if (cmd == 1) {
            heater_on = false;
            digitalWrite(PIN_RELAY, LOW);
            Serial.println(F("# Heater OFF"));
        } else if (cmd == 2) {
            heater_on = true;
            digitalWrite(PIN_RELAY, HIGH);
            Serial.println(F("# Heater ON"));
        } else if (cmd == 9) {
            // dump all current values
            sampleAndLog();
        }
    }
}

