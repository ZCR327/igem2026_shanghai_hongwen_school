#include <DFString.h>
#include <DFRobot_PH.h>
#include <DFRobot_SCD4X.h>
#include <DFRobot_DS18B20.h>
#include <DFRobot_OxygenSensor.h>

// 动态变量
String         mind_s_Serial_data;
volatile float mind_n_times, mind_n_last_temp;

// 创建对象
DFRobot_DS18B20 ds18b20_47;
DFRobot_PH2 ph2;
DFRobot_SCD4X SCD4X(&Wire, 0x62);
DFRobot_OxygenSensor Oxygen;

void DF_end_data();
void DF_mega2560_Reading_environmental_sensor_data(float mind_n_time);
void DF_stir_stick_control(String mind_s_string);
void DF_temperature_control(float mind_n_temp);
void DF_temp_setting(String mind_s_data);
void DF_setup();

// 主程序开始
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
	DF_mega2560_Reading_environmental_sensor_data(5000);
	if ((Serial1.available())) {
		mind_s_Serial_data = (String(Serial1.read()));
		DF_temp_setting(mind_s_Serial_data);
		DF_stir_stick_control(mind_s_Serial_data);
	}
}


// 自定义函数
void DF_end_data() {
	Serial1.write(255);
	Serial1.write(255);
	Serial1.write(255);
	Serial1.println();
}
void DF_mega2560_Reading_environmental_sensor_data(float mind_n_time) {
	if (((millis() - mind_n_times)>=mind_n_time)) {
		mind_n_last_temp = millis();
		Serial1.print("t7.txt=");
		Serial1.print(ds18b20_47.getTempC());
		DF_end_data();
		if ((SCD4X.getDataReadyStatus())) {
			DFRobot_SCD4X::sSensorMeasurement_t data;
			SCD4X.readMeasurement(&data);
			Serial1.print("t8.txt=");
			Serial1.print((data.temp));
			DF_end_data();
		}
		Serial1.print("t9.txt=");
		Serial1.print((Oxygen.ReadOxygenData(10)));
		DF_end_data();
		if ((SCD4X.getDataReadyStatus())) {
			DFRobot_SCD4X::sSensorMeasurement_t data;
			SCD4X.readMeasurement(&data);
			Serial1.print("t10.txt=");
			Serial1.print((data.CO2ppm));
			DF_end_data();
		}
		Serial1.print("t11.txt=");
		Serial1.print(ph2.readPH(A6));
		DF_end_data();
	}
}
void DF_stir_stick_control(String mind_s_string) {
	if ((mind_s_string=="a")) {
		digitalWrite(41, HIGH);
	}
	if ((mind_s_string=="b")) {
		digitalWrite(41, LOW);
	}
	if ((mind_s_string=="c")) {
		digitalWrite(42, HIGH);
	}
	if ((mind_s_string=="d")) {
		digitalWrite(42, LOW);
	}
	if ((mind_s_string=="e")) {
		digitalWrite(43, HIGH);
	}
	if ((mind_s_string=="f")) {
		digitalWrite(43, LOW);
	}
	if ((mind_s_string=="g")) {
		digitalWrite(41, HIGH);
	}
	if ((mind_s_string=="h")) {
		digitalWrite(41, LOW);
	}
}
void DF_temperature_control(float mind_n_temp) {
	if (((ds18b20_47.getTempC()>(mind_n_temp + 2)) || (ds18b20_47.getTempC()<(mind_n_temp - 2)))) {
		if ((ds18b20_47.getTempC()>mind_n_temp)) {
			while (!((abs((ds18b20_47.getTempC() - mind_n_temp)))<1)) {
				digitalWrite(46, HIGH);
				yield();
			}
		}
		digitalWrite(46, LOW);
		if ((ds18b20_47.getTempC()<mind_n_temp)) {
			while (!((abs((ds18b20_47.getTempC() - mind_n_temp)))<1)) {
				digitalWrite(45, HIGH);
				yield();
			}
		}
		digitalWrite(45, LOW);
	}
}
void DF_temp_setting(String mind_s_data) {
	if (((String(mind_s_data).length())==6)) {
		if (((String(mind_s_data).indexOf(String("temp")) != -1))) {
			mind_n_last_temp = (String((dfstring.substring(mind_s_data,1,2,1,1))).toFloat());
			DF_temperature_control(mind_n_last_temp);
		}
		if (((String(mind_s_data).indexOf(String("temp")) != -1))) {
			mind_n_last_temp = (String((dfstring.substring(mind_s_data,1,2,1,1))).toFloat());
			DF_temperature_control(mind_n_last_temp);
		}
	}
	if (((String(mind_s_data).length())==8)) {
		if (((String(mind_s_data).indexOf(String("temp")) != -1))) {
			mind_n_last_temp = (String((dfstring.substring(mind_s_data,1,4,1,1))).toFloat());
			DF_temperature_control(mind_n_last_temp);
		}
		if (((String(mind_s_data).indexOf(String("temp")) != -1))) {
			mind_n_last_temp = (String((dfstring.substring(mind_s_data,1,4,1,1))).toFloat());
			DF_temperature_control(mind_n_last_temp);
		}
	}
}
void DF_setup() {
	Serial1.begin(115200);
	mind_n_last_temp = 0;
	mind_n_times = 0;
	mind_s_Serial_data = "";
}

