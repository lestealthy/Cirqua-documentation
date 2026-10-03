
void Task_UART_Node2(void* pvParameters) {
  SerialNode1.begin(INTERNODE_BAUD, SERIAL_8N1, PIN_N1_UART_RX, PIN_N1_UART_TX);
  SerialNode3.begin(INTERNODE_BAUD, SERIAL_8N1, PIN_N3_UART_RX, PIN_N3_UART_TX);

  char rxBufferN1[128], rxBufferN3[128];
  size_t rxIdxN1 = 0, rxIdxN3 = 0;

  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xFrequency = pdMS_TO_TICKS(50);  // 20 Hz Polling

  for (;;) {
    vTaskDelayUntil(&xLastWakeTime, xFrequency);

    // ----------------------------------------------------
    // 1. Read Upstream Telemetry from Node 1
    // ----------------------------------------------------
    while (SerialNode1.available() > 0) {
      char c = (char)SerialNode1.read();
      if (c == '\n' || c == '\r') continue;
      if (rxIdxN1 < sizeof(rxBufferN1) - 1) {
        rxBufferN1[rxIdxN1++] = c;
      } else {
        rxIdxN1 = 0;  // Buffer overflow safety reset
      }

      if (c == ';') {
        rxBufferN1[rxIdxN1] = '\0';
        Node1Telemetry parsedN1 = { 0 };
        if (parseNode1Packet(rxBufferN1, parsedN1)) {
          if (xSemaphoreTake(xN1DataMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            g_n1Data = parsedN1;
            xSemaphoreGive(xN1DataMutex);
          }
        }
        rxIdxN1 = 0;
      }
    }

    // ----------------------------------------------------
    // 2. Read Reverse Telemetry from Node 3
    // ----------------------------------------------------
    while (SerialNode3.available() > 0) {
      char c = (char)SerialNode3.read();
      if (c == '\n' || c == '\r') continue;
      if (rxIdxN3 < sizeof(rxBufferN3) - 1) {
        rxBufferN3[rxIdxN3++] = c;
      } else {
        rxIdxN3 = 0;  // Buffer overflow safety reset
      }

      if (c == ';') {
        rxBufferN3[rxIdxN3] = '\0';
        Node3ReverseTelemetry parsedN3 = { 0 };
        if (parseNode3ReversePacket(rxBufferN3, parsedN3)) {
          if (xSemaphoreTake(xN3DataMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            g_n3Data = parsedN3;  // Fixed variable target
            xSemaphoreGive(xN3DataMutex);
          }
        }
        rxIdxN3 = 0;
      }
    }

    // ----------------------------------------------------
    // 3. Construct Consolidated Payload & Send Downstream to Node 3
    // ----------------------------------------------------
    Node2Sensors sSnap = { 0 };
    Node1Telemetry n1Snap = { 0 };

    if (xSemaphoreTake(xSensorsMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
      sSnap = g_n2Sensors;
      xSemaphoreGive(xSensorsMutex);
    }
    if (xSemaphoreTake(xN1DataMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
      n1Snap = g_n1Data;
      xSemaphoreGive(xN1DataMutex);
    }

    // Compute overall Node 2 status dynamically based on validity flags
    bool node2Healthy = sSnap.tempValid && sSnap.doValid && sSnap.tbvValid && sSnap.atValid && sSnap.ahValid;

    char downstreamPayload[256];
    snprintf(downstreamPayload, sizeof(downstreamPayload),
             "|TAV:%.2f|node1:%d|DO:%.2f|Temp:%.2f|TBV:%.2f|AT:%.2f|AH:%.2f|node2:%d;\n",
             n1Snap.isValid ? n1Snap.tav : 0.0f,
             (n1Snap.isValid && n1Snap.node1Status) ? 1 : 0,
             sSnap.doValid ? sSnap.doVal : 0.0f,
             sSnap.tempValid ? sSnap.temp : 0.0f,
             sSnap.tbvValid ? sSnap.tbv : 0.0f,
             sSnap.atValid ? sSnap.at : 0.0f,
             sSnap.ahValid ? sSnap.ah : 0.0f,
             node2Healthy ? 1 : 0);

    SerialNode3.print(downstreamPayload);

    // ----------------------------------------------------
    // 4. Echo Upstream Telemetry back to Node 1 for Local Display
    // ----------------------------------------------------
    char echoToN1[256];
    snprintf(echoToN1, sizeof(echoToN1),
             "|DO:%.2f|Temp:%.2f|TBV:%.2f|AT:%.2f|AH:%.2f|node2:%d;\n",
             sSnap.doValid ? sSnap.doVal : 0.0f,
             sSnap.tempValid ? sSnap.temp : 0.0f,
             sSnap.tbvValid ? sSnap.tbv : 0.0f,
             sSnap.atValid ? sSnap.at : 0.0f,
             sSnap.ahValid ? sSnap.ah : 0.0f,
             node2Healthy ? 1 : 0);

    SerialNode1.print(echoToN1);
  }
}
