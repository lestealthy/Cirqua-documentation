// ============================================================
void Task_Sensors_Node1(void *pvParameters) {
    pinMode(PIN_N1_TRIG, OUTPUT);
    pinMode(PIN_N1_ECHO, INPUT);
    digitalWrite(PIN_N1_TRIG, LOW);

    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(500);

    for (;;) {
        vTaskDelayUntil(&xLastWakeTime, xFrequency);

        digitalWrite(PIN_N1_TRIG, LOW);
        delayMicroseconds(2);
        digitalWrite(PIN_N1_TRIG, HIGH);
        delayMicroseconds(10);
        digitalWrite(PIN_N1_TRIG, LOW);

        unsigned long duration = pulseIn(PIN_N1_ECHO, HIGH, 30000); // 30ms timeout
        
        LocalSensorData currentRead = {0, false};

        if (duration > 0) {
            // True 0-offset ultrasonic calculation
            float distance = (duration * 0.0343f / 2.0f);
            float waterHeight = TANK_HEIGHT - distance;
            if (waterHeight < 0.0f) waterHeight = 0.0f;

            float volumeLiters = (3.14159f * TANK_RADIUS * TANK_RADIUS * waterHeight) / 1000.0f;
            
            currentRead.volumeLiters = (int)(volumeLiters * 2.0f);
            currentRead.isValid = true;
        }

        if (xSemaphoreTake(xLocalDataMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
            g_localSensors = currentRead;
            xSemaphoreGive(xLocalDataMutex);
        }
    }
}
