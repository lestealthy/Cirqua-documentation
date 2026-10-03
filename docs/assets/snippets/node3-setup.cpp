// ============================================================
void setup() {
    Serial.begin(115200);

    xFlowMutex = xSemaphoreCreateMutex();
    if (!xFlowMutex) systemFatalTrap("Mutex Allocation");

    BaseType_t r1 = xTaskCreatePinnedToCore(Task_Flow_Node3, "N3_Flow", 3072, NULL, 2, NULL, 1);
    BaseType_t r2 = xTaskCreatePinnedToCore(Task_UART_Node3, "N3_UART", 3072, NULL, 3, NULL, 0);

    if (r1 != pdPASS) systemFatalTrap("N3_Flow Task Creation");
    if (r2 != pdPASS) systemFatalTrap("N3_UART Task Creation");
}
