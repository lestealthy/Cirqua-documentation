        // Periodic Background Checks (Heartbeat every 24h, Error Checks with 12h cooldown)
        time_t currentEpoch = time(nullptr);

        // Heartbeat Check (Every 24 Hours = 86400 seconds)
        if (currentEpoch - lastHeartbeatEpoch >= 86400) {
            char hbMsg[256];
            snprintf(hbMsg, sizeof(hbMsg), 
                     "<p><b>Node 4 Status:</b> Operating normally.</p><p>Timestamp: %s</p>", ctime(&currentEpoch));
            if (sendMailMessage("[WattLab Node 4] Daily Heartbeat OK", hbMsg)) {
                lastHeartbeatEpoch = currentEpoch;
                preferences.begin("email_state", false);
                preferences.putULong("lastHbEpoch", lastHeartbeatEpoch);
                preferences.end();
            }
        }

        // Error & Environmental Alert Check (With 12-Hour Cooldown = 43200 seconds)
        LocalNode4Data checkSnap = {0};
        if (xSemaphoreTake(xLocalN4Mutex, pdMS_TO_TICKS(20)) == pdTRUE) {
            checkSnap = g_localN4;
            xSemaphoreGive(xLocalN4Mutex);
        }

        bool hasError = (!checkSnap.phValid || !checkSnap.ntuValid || !checkSnap.ecValid || 
                         !checkSnap.subTempValid || !checkSnap.ambTempValid || !checkSnap.ambHumValid || !checkSnap.evValid ||
                         checkSnap.ambTemp > 45.0f || checkSnap.ambHum > 90.0f);

        if (hasError && (currentEpoch - lastErrorEmailEpoch >= 43200)) {
            String errorDetails = "<ul>";
            if (!checkSnap.phValid) errorDetails += "<li>pH Sensor Fault / Out of Range</li>";
            if (!checkSnap.ntuValid) errorDetails += "<li>Turbidity Sensor Fault</li>";
            if (!checkSnap.ecValid) errorDetails += "<li>EC Sensor Fault</li>";
            if (!checkSnap.subTempValid) errorDetails += "<li>Submerged DS18B20 Temp Sensor Disconnected/Fault</li>";
            if (!checkSnap.ambTempValid || checkSnap.ambTemp > 45.0f) errorDetails += "<li>Ambient Temperature Fault or Excessive (>45C)</li>";
            if (!checkSnap.ambHumValid || checkSnap.ambHum > 90.0f) errorDetails += "<li>Ambient Humidity Fault or Excessive (>90%)</li>";
            if (!checkSnap.evValid) errorDetails += "<li>Effluent Ultrasonic Tank Sensor Fault</li>";
            errorDetails += "</ul>";

            char errHtml[512];
            snprintf(errHtml, sizeof(errHtml), 
                     "<p><b>ATTENTION:</b> Sensor fault or excessive ambient conditions detected on Node 4!</p>%s<p>Time: %s</p>", 
                     errorDetails.c_str(), ctime(&currentEpoch));

            if (sendMailMessage("[WattLab Node 4] FAULT ALERT", errHtml)) {
                lastErrorEmailEpoch = currentEpoch;
                preferences.begin("email_state", false);
                preferences.putULong("lastErrEpoch", lastErrorEmailEpoch);
                preferences.end();
            }
        }
