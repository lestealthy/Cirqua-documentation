
void setup() {
  Serial.begin(115200);

  // Create RTOS Mutexes
  xSensorsMutex = xSemaphoreCreateMutex();
  xN1DataMutex = xSemaphoreCreateMutex();
  xN3DataMutex = xSemaphoreCreateMutex();

  if (!xSensorsMutex || !xN1DataMutex || !xN3DataMutex) {
    systemFatalTrap("Mutex Allocation Failure");
  }

  // Pin Sensor Task to Core 1, UART Communication Task to Core 0
  BaseType_t r1 = xTaskCreatePinnedToCore(Task_Sensors_Node2, "N2_Sensors", 4096, NULL, 2, NULL, 1);
  BaseType_t r2 = xTaskCreatePinnedToCore(Task_UART_Node2, "N2_UART", 4096, NULL, 3, NULL, 0);

  if (r1 != pdPASS) systemFatalTrap("Task N2_Sensors Creation");
  if (r2 != pdPASS) systemFatalTrap("Task N2_UART Creation");
}
