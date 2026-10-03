// ============================================================
void Task_UART_Node1(void *pvParameters) {
    String rxBuffer = "";
    rxBuffer.reserve(256);

    uint32_t lastTxTime = 0;

    for (;;) {
        while (NodeSerial.available() > 0) {
            char c = (char)NodeSerial.read();

            if (c == '\n') {
                rxBuffer.trim();
                if (rxBuffer.length() > 0) {
                    processNode2Packet(rxBuffer);
                }
                rxBuffer = "";
            } else if (c != '\r') {
                rxBuffer += c;
                if (rxBuffer.length() > 250) {
                    rxBuffer = "";
                }
            }
        }

        uint32_t now = millis();
        if (now - lastTxTime >= TX_INTERVAL_MS) {
            lastTxTime = now;

            LocalSensorData localSnap = {0, false};
            if (xSemaphoreTake(xLocalDataMutex, pdMS_TO_TICKS(10)) == pdTRUE) {
                localSnap = g_localSensors;
                xSemaphoreGive(xLocalDataMutex);
            }

            // Standardized with leading pipe
            String outboundData = "|TAV:" + String(localSnap.volumeLiters) + 
                                  "|node1:" + String(localSnap.isValid ? 1 : 0) + ";\n";
            NodeSerial.print(outboundData);
        }

        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
