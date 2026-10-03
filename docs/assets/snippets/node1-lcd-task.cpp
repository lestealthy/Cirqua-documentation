
void Task_LCD_Node1(void *pvParameters) {
    lcd.begin(16, 4);
    lcd.backlight();

    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(500);

    for (;;) {
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        LocalSensorData localSnap = {0, false};
        Node2Telemetry node2Snap = {-1.0f, -127.0f, -1, -127.0f, -1.0f, false, false};
        uint32_t lastRx = 0;

        if (xSemaphoreTake(xLocalDataMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            localSnap = g_localSensors;
            xSemaphoreGive(xLocalDataMutex);
        }
        if (xSemaphoreTake(xNode2DataMutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            node2Snap = g_node2Data;
            lastRx = g_lastNode2Rx;
            xSemaphoreGive(xNode2DataMutex);
        }

        // Line 1: Tank Volumes (Strictly aligned to fit <= 16 chars)
        String line1 = "C" + String(localSnap.volumeLiters) + "L F";
        if (node2Snap.volume >= 0) line1 += String(node2Snap.volume);
        else line1 += "----";
        line1 += "L";

        // Line 2: DO (mg/l) & Water Temp (Optimized to fit exactly within 16 chars)
        String line2 = "DO";
        if (node2Snap.doVal >= 0) line2 += String(node2Snap.doVal, 1);
        else line2 += "--";
        line2.replace(".", ",");

        line2 += "mg/l T";
        if (node2Snap.waterTemp > -100.0f) line2 += String(node2Snap.waterTemp, 1);
        else line2 += "--";
        line2.replace(".", ",");
        line2 += "C";

        // Line 3: Ambient Temp & Humidity
        String line3 = "AT";
        if (node2Snap.ambientTemp > -100.0f) line3 += String(node2Snap.ambientTemp, 1);
        else line3 += "--";
        line3.replace(".", ",");

        line3 += "C H";
        if (node2Snap.humidity >= 0) line3 += String(node2Snap.humidity, 0);
        else line3 += "--";
        line3 += "%";

        // Line 4: Environmental, Volume & Communication System Status
        String statusStr = "NORMAL";

        bool highTemp  = (node2Snap.ambientTemp >= TEMP_ALERT_TH);
        bool highHumid = (node2Snap.humidity >= HUMID_ALERT_TH);

        bool lowTav    = localSnap.isValid && (localSnap.volumeLiters < TAV_LOW_ALERT_TH);
        bool lowTbv    = (node2Snap.volume >= 0) && (node2Snap.volume < TBV_LOW_ALERT_TH);

        if (lastRx == 0) {
            statusStr = "WAITING";      // Waiting for initial frame
        } else if (millis() - lastRx > RX_TIMEOUT_MS) {
            statusStr = "ERROR";         // Serial link dead
        } else if (highTemp && highHumid) {
            statusStr = "HOT+HUM";       // High temperature & high moisture
        } else if (highTemp) {
            statusStr = "OVERTEMP";      // Enclosure overheat alert
        } else if (highHumid) {
            statusStr = "HI HUMID";      // Enclosure condensation alert
        } else if (lowTav && lowTbv) {
            statusStr = "LOW C+F";       // Both Collection (TAV) and Feeding (TBV) tanks low
        } else if (lowTav) {
            statusStr = "LOW TAV";       // Collection tank (TAV < 5000L) low
        } else if (lowTbv) {
            statusStr = "LOW TBV";       // Feeding tank (TBV < 500L) low
        } else if (!node2Snap.node2Health) {
            statusStr = "FAULT";         // Hardware sensor error on Node 2
        }

        String line4 = "STATUS: " + statusStr;

        printLCDLine(0, line1);
        printLCDLine(1, line2);
        printLCDLine(2, line3);
        printLCDLine(3, line4);
    }
}
