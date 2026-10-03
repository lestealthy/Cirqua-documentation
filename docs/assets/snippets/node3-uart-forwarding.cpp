// ============================================================
void Task_UART_Node3(void *pvParameters) {
    UpstreamSerial.begin(INTERNODE_BAUD, SERIAL_8N1, PIN_UP_UART_RX, PIN_UP_UART_TX);
    DownstreamSerial.begin(INTERNODE_BAUD, SERIAL_8N1, PIN_DOWN_UART_RX, PIN_DOWN_UART_TX);

    char rxBuffer[256];
    size_t rxIdx = 0;
    uint32_t lastUpstreamRxTime = millis();
    bool timeoutAlertSent = false;

    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(50);

    for (;;) {
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        FlowData fSnap = {0.0f, false};
        if (xSemaphoreTake(xFlowMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            fSnap = g_flowData;
            xSemaphoreGive(xFlowMutex);
        }

        bool receivedNewFrame = false;

        // Process incoming stream from Node 2
        while (UpstreamSerial.available() > 0) {
            char c = (char)UpstreamSerial.read();
            if (c == '\n' || c == '\r') continue;

            if (rxIdx < sizeof(rxBuffer) - 1) {
                rxBuffer[rxIdx++] = c;
            } else {
                rxIdx = 0; // Prevent buffer overflow
            }

            if (c == ';') {
                rxBuffer[rxIdx] = '\0';

                if (validateUpstreamFrame(rxBuffer)) {
                    // Strip trailing delimiter
                    if (rxIdx > 0 && rxBuffer[rxIdx - 1] == ';') {
                        rxBuffer[rxIdx - 1] = '\0';
                    }

                    char clusterPacket[320];
                    // Standardized key name FLM for downstream controller compatibility
                    snprintf(clusterPacket, sizeof(clusterPacket), "%s|FLM:%.2f|node3:%d;\n",
                             rxBuffer,
                             fSnap.isValid ? fSnap.flowRate : 0.0f,
                             fSnap.isValid ? 1 : 0);

                    DownstreamSerial.print(clusterPacket);
                    lastUpstreamRxTime = millis();
                    timeoutAlertSent = false;
                    receivedNewFrame = true;
                }
                rxIdx = 0;
            }
        }

        // Upstream Timeout Fallback Transmission
        if (!receivedNewFrame && (millis() - lastUpstreamRxTime > TIMEOUT_MS) && !timeoutAlertSent) {
            char fallbackPacket[128];
            snprintf(fallbackPacket, sizeof(fallbackPacket),
                     "|TAV:0.00|node1:0|DO:0.00|node2:0|FLM:%.2f|node3:%d;\n",
                     fSnap.isValid ? fSnap.flowRate : 0.0f,
                     fSnap.isValid ? 1 : 0);

            DownstreamSerial.print(fallbackPacket);
            timeoutAlertSent = true; // Mute spam until link recovers
        }
    }
}
