#define INTERNODE_BAUD 9600

#define PIN_DS18B20 4
#define PIN_DO_ANALOG 34
#define PIN_N2_TRIG 16
#define PIN_N2_ECHO 17
#define PIN_DHT11 27
#define PIN_N1_UART_RX 25
#define PIN_N1_UART_TX 26
#define PIN_N3_UART_RX 32
#define PIN_N3_UART_TX 33

#define DHTTYPE DHT11

// DO Sensor Electrical Calibration Constants
const float VREF = 5000.0f;               // ADC Reference Voltage (mV) on 3.3V ESP32
const float ADC_RESOLUTION = 4095.0f;     // 12-bit ADC
const float TWO_POINT_VOLTAGE = 1000.0f;  // Calibration voltage threshold (mV)
const float SATURATION_DO_25C = 8.26f;    // Saturation DO concentration mg/L at 25°C

// Physical Tank Geometry (cm)
const float TANK_HEIGHT = 178.0f;
const float TANK_RADIUS = 59.5f;
