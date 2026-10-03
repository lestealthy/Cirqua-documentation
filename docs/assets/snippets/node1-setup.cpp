// ============================================================
void setup() {
    Serial.begin(115200);

    Wire.begin(PIN_LCD_SDA, PIN_LCD_SCL);
    NodeSerial.begin(INTERNODE_BAUD, SERIAL_8N1, PIN_N1_UART_RX, PIN_N1_UART_TX);

    xLocalDataMutex = xSemaphoreCreateMutex();
    xNode2DataMutex = xSemaphoreCreateMutex();

    if (!xLocalDataMutex || !xNode2DataMutex) {
        systemFatalTrap("Mutex Allocation");
    }

    BaseType_t r1 = xTaskCreatePinnedToCore(Task_Sensors_Node1, "N1_Sensors", 3072, NULL, 2, NULL, 1);
    BaseType_t r2 = xTaskCreatePinnedToCore(Task_UART_Node1,    "N1_UART",    3072, NULL, 3, NULL, 0);
    BaseType_t r3 = xTaskCreatePinnedToCore(Task_LCD_Node1,     "N1_LCD",     3072, NULL, 1, NULL, 1);

    if (r1 != pdPASS) systemFatalTrap("N1_Sensors Task");
    if (r2 != pdPASS) systemFatalTrap("N1_UART Task");
    if (r3 != pdPASS) systemFatalTrap("N1_LCD Task");
}
