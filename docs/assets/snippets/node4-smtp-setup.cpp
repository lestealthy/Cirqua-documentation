// ============================================================
void setup() {
    Serial.begin(115200);
    delay(500);

    loadCalibration();

    // Initialize Wi-Fi and Synchronize Time before creating network tasks
    initNetworkAndTime();

    xLocalN4Mutex = xSemaphoreCreateMutex();
    if (!xLocalN4Mutex) systemFatalTrap("Mutex Allocation");

    BaseType_t r1 = xTaskCreatePinnedToCore(Task_Sensors_Node4,         "N4_Sensors", 4096, NULL, 2, NULL, 1);
    BaseType_t r2 = xTaskCreatePinnedToCore(Task_Email_And_UART_Node4,  "N4_EmailUART", 5120, NULL, 3, NULL, 0);
    BaseType_t r3 = xTaskCreatePinnedToCore(Task_LCD_Node4,             "N4_LCD",     3072, NULL, 1, NULL, 1);

    if (r1 != pdPASS) systemFatalTrap("N4_Sensors Task");
    if (r2 != pdPASS) systemFatalTrap("N4_EmailUART Task");
    if (r3 != pdPASS) systemFatalTrap("N4_LCD Task");
}
