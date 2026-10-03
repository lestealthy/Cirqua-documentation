#define INTERNODE_BAUD 9600

// Hardware Pin Assignments
#define PIN_EFFLUENT_TRIG 4
#define PIN_EFFLUENT_ECHO 2
#define PIN_PH_ANALOG     13
#define PIN_TURB_ANALOG   14
#define PIN_EC_ANALOG     12
#define PIN_SUB_DS18B20   27
#define PIN_N4_DHT11      5

#define PIN_N4_UART_RX    25  // From Node 3
#define PIN_N4_UART_TX    26
#define PIN_N5_UART_RX    32  // To Controller (Mega)
#define PIN_N5_UART_TX    33

#define PIN_N4_LCD_SDA    21
#define PIN_N4_LCD_SCL    22

#define DHTTYPE           DHT11

// IMPORTANT:
// ESP32 ADC is NOT a true 0-5V ADC.
// The sensor boards may be powered from 5V, but their analog
// output must remain within the ESP32 ADC input range.
//
// ADC attenuation is configured below.
#define ADC_RESOLUTION    4095.0f

// Tank Geometry (cm)
const float TANK_HEIGHT = 178.0f;
const float TANK_RADIUS = 59.5f;
