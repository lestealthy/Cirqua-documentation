
void Task_UART_Node4(void *pvParameters) {

    UpstreamSerial.begin(
        INTERNODE_BAUD,
        SERIAL_8N1,
        PIN_N4_UART_RX,
        PIN_N4_UART_TX
    );

    DownstreamSerial.begin(
        INTERNODE_BAUD,
        SERIAL_8N1,
        PIN_N5_UART_RX,
        PIN_N5_UART_TX
    );

    char rxBuffer[384];

    size_t rxIdx = 0;

    TickType_t xLastWakeTime =
        xTaskGetTickCount();

    const TickType_t xFrequency =
        pdMS_TO_TICKS(50);

    for (;;) {

        vTaskDelayUntil(
            &xLastWakeTime,
            xFrequency
        );

        handleSerialCalibrationCommands();

        while (UpstreamSerial.available() > 0) {

            char c =
                (char)UpstreamSerial.read();

            if (c == '\n' ||
                c == '\r') {

                continue;
            }

            if (rxIdx <
                sizeof(rxBuffer) - 1) {

                rxBuffer[rxIdx++] = c;

            } else {

                rxIdx = 0;
            }

            if (c == ';') {

                rxBuffer[rxIdx] = '\0';

                if (
                    rxIdx > 0 &&
                    rxBuffer[rxIdx - 1] == ';'
                ) {

                    rxBuffer[rxIdx - 1] =
                        '\0';
                }

                LocalNode4Data n4Snap = {0};

                if (
                    xSemaphoreTake(
                        xLocalN4Mutex,
                        pdMS_TO_TICKS(20)
                    ) == pdTRUE
                ) {

                    n4Snap = g_localN4;

                    xSemaphoreGive(
                        xLocalN4Mutex
                    );
                }

                String cleanedUpstream =
                    cleanUpstreamPacket(
                        String(rxBuffer)
                    );

                Serial.println(
                    "\n================ [NODE 4 PACKET TRANSACTION] ================"
                );

                Serial.printf(
                    "[INCOMING] Raw Packet from Upstream: %s;\n",
                    rxBuffer
                );

                Serial.printf(
                    "[CLEANED] Upstream Packet: %s\n",
                    cleanedUpstream.c_str()
                );

                Serial.println(
                    "[LOCAL SENSORS] Current Node 4 Readings:"
                );

                Serial.printf(
                    "  - pH:       %.1f (Valid: %s)\n",
                    n4Snap.ph,
                    n4Snap.phValid
                        ? "YES"
                        : "NO"
                );

                Serial.printf(
                    "  - Turbidity:%.1f NTU (Valid: %s)\n",
                    n4Snap.ntu,
                    n4Snap.ntuValid
                        ? "YES"
                        : "NO"
                );

                Serial.printf(
                    "  - EC:       %.0f uS/cm (Valid: %s)\n",
                    n4Snap.ec,
                    n4Snap.ecValid
                        ? "YES"
                        : "NO"
                );

                Serial.printf(
                    "  - TCV Volume:%d L (Valid: %s)\n",
                    n4Snap.tcVolume,
                    n4Snap.tcValid
                        ? "YES"
                        : "NO"
                );

                static char fullPacket[512];

                snprintf(
                    fullPacket,
                    sizeof(fullPacket),

                    "%s|pH:%.1f|Turb:%d|EC:%.0f|TCV:%d|node4:1;\n",

                    cleanedUpstream.c_str(),

                    n4Snap.phValid
                        ? n4Snap.ph
                        : 0.0f,

                    n4Snap.ntuValid
                        ? (int)n4Snap.ntu
                        : 0,

                    n4Snap.ecValid
                        ? n4Snap.ec
                        : 0.0f,

                    n4Snap.tcValid
                        ? n4Snap.tcVolume
                        : 0
                );

                Serial.printf(
                    "[OUTGOING] Final Packet Sent Downstream: %s",
                    fullPacket
                );

                Serial.println(
                    "=============================================================\n"
                );

                DownstreamSerial.print(
                    fullPacket
                );

                rxIdx = 0;
            }
        }
    }
}
