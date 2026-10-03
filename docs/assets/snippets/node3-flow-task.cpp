// ============================================================
void Task_Flow_Node3(void *pvParameters) {
    pinMode(PIN_FLOW_SENSOR, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_FLOW_SENSOR), pulseISR, FALLING);

    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(1000);

    for (;;) {
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        uint32_t pulses = 0;
        portENTER_CRITICAL(&g_pulseMux);
        pulses = g_pulseCount;
        g_pulseCount = 0;
        portEXIT_CRITICAL(&g_pulseMux);

        FlowData currentFlow;
        currentFlow.flowRate = (float)pulses / FLOW_CAL_FACTOR; // L/min
        currentFlow.isValid = true;

        if (xSemaphoreTake(xFlowMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            g_flowData = currentFlow;
            xSemaphoreGive(xFlowMutex);
        }
    }
}
