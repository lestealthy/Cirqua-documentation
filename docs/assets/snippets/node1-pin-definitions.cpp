#define INTERNODE_BAUD 9600

// ============================================================
// HARDWARE PIN ASSIGNMENTS
// ============================================================
#define PIN_N1_TRIG      2
#define PIN_N1_ECHO      17

// Node 1 <-> Node 2 (Bidirectional UART)
#define PIN_N1_UART_RX   32
#define PIN_N1_UART_TX   33

#define PIN_LCD_SDA      21
#define PIN_LCD_SCL      22

// ============================================================
// SYSTEM THRESHOLDS & TANK GEOMETRY
// ============================================================
const float TANK_HEIGHT     = 260.0f;
const float TANK_RADIUS     = 110.0f;

// Environmental Safety Thresholds (Node 2 Enclosure)
const float TEMP_ALERT_TH   = 45.0f;  // Deg C (Overheat threshold)
const float HUMID_ALERT_TH  = 80.0f;  // % RH (Condensation threshold)

// Low Volume Alert Thresholds (in Liters)
const int TAV_LOW_ALERT_TH   = 5000;   // Collection Tank A Low Threshold (< 5000L)
const int TBV_LOW_ALERT_TH   = 500;    // Feeding Tank B Low Threshold (< 500L)

#define RX_TIMEOUT_MS       3000
#define TX_INTERVAL_MS      500
