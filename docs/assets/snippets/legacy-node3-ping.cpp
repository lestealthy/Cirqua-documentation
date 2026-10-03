#include <Arduino.h>

HardwareSerial InSerial(1);  // RX=25, TX=26
HardwareSerial OutSerial(2); // RX=32, TX=33

const String NODE_NAME = "node3";
unsigned long lastReceivedTime = 0;
const unsigned long TIMEOUT_MS = 2000;

const byte SENSOR_PIN = 23;          
volatile uint16_t pulseCount = 0;    
float flowRate = 0.0;
unsigned long lastFlowMillis = 0;
const float CALIBRATION_FACTOR = 5.5; 

void IRAM_ATTR pulseCounterISR() {
  pulseCount++;
}

void setup() {
  Serial.begin(115200);
  InSerial.begin(9600, SERIAL_8N1, 25, 26);
  InSerial.setTimeout(50);
  OutSerial.begin(9600, SERIAL_8N1, 32, 33);
  
  pinMode(SENSOR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(SENSOR_PIN), pulseCounterISR, FALLING);
  
  lastReceivedTime = millis();
  lastFlowMillis = millis();
}

float getFLM() {
  if (millis() - lastFlowMillis >= 1000) {
    noInterrupts(); 
    uint16_t currentPulses = pulseCount;
    pulseCount = 0;   
    interrupts();   
    
    flowRate = (float)currentPulses / CALIBRATION_FACTOR;
