
void Task_Sensors_Node2(void* pvParameters) {
  sensorsN2.begin();
  sensorsN2.setWaitForConversion(false);  // Non-blocking state machine
  sensorsN2.requestTemperatures();        // Trigger initial conversion

  dhtN2.begin();

  pinMode(PIN_N2_TRIG, OUTPUT);
  pinMode(PIN_N2_ECHO, INPUT);
  digitalWrite(PIN_N2_TRIG, LOW);

  analogReadResolution(12);

  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xFrequency = pdMS_TO_TICKS(1000);  // 1 Hz Periodic Loop

  TickType_t xLastDHTTick = 0;

  for (;;) {
    vTaskDelayUntil(&xLastWakeTime, xFrequency);
    TickType_t now = xTaskGetTickCount();

    Node2Sensors localSnap = { 0 };

    // Fetch current values under lock to keep prior valid state if needed
    if (xSemaphoreTake(xSensorsMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
      localSnap = g_n2Sensors;
      xSemaphoreGive(xSensorsMutex);
    }

    // ----------------------------------------------------
    // 1. DS18B20 Water Temperature (Non-Blocking)
    // ----------------------------------------------------
    float tempC = sensorsN2.getTempCByIndex(0);
    sensorsN2.requestTemperatures();  // Trigger conversion for NEXT cycle

    if (tempC != DEVICE_DISCONNECTED_C && tempC > -55.0f && tempC < 125.0f) {
      localSnap.temp = tempC;
      localSnap.tempValid = true;
    } else {
      localSnap.tempValid = false;
    }

    // ----------------------------------------------------
    // 2. Dissolved Oxygen (DO) + Temperature Compensation
    // ----------------------------------------------------
    int rawDO = analogRead(PIN_DO_ANALOG);
    if (rawDO > 0) {
      float doVoltage = ((float)rawDO / ADC_RESOLUTION) * VREF;  // Voltage in mV

      // Temperature compensation factor relative to 25°C
      float compTemp = localSnap.tempValid ? localSnap.temp : 25.0f;
      float compFactor = 1.0f + (compTemp - 25.0f) * (-0.02f);

      float dissolvedOxygen = (doVoltage / TWO_POINT_VOLTAGE) * SATURATION_DO_25C * compFactor;
      if (dissolvedOxygen < 0.0f) dissolvedOxygen = 0.0f;

      localSnap.doVal = dissolvedOxygen;
      localSnap.doValid = true;
    } else {
      localSnap.doValid = false;
    }

    // ----------------------------------------------------
    // 3. Ultrasonic Feeding Tank B Volume (TBV)
    // ----------------------------------------------------
    digitalWrite(PIN_N2_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_N2_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_N2_TRIG, LOW);

    unsigned long duration = pulseIn(PIN_N2_ECHO, HIGH, 20000);  // 20ms timeout (~3.4m)
    if (duration > 0) {
      // Distance in cm
      float distanceCm = (duration * 0.0343f) / 2.0f;

      // Water height in cm (TANK_HEIGHT = 178.0 cm)
      float waterHeight = TANK_HEIGHT - distanceCm;
      if (waterHeight < 0.0f) waterHeight = 0.0f;
      if (waterHeight > TANK_HEIGHT) waterHeight = TANK_HEIGHT;

      // Cylinder Volume in Liters: (pi * r^2 * h) / 1000
      // TANK_RADIUS = 59.5 cm
      float volumeLiters = (3.14159f * TANK_RADIUS * TANK_RADIUS * waterHeight) / 1000.0f;

      localSnap.tbv = volumeLiters;
      localSnap.tbvValid = true;
    } else {
      localSnap.tbvValid = false;
    }

    // ----------------------------------------------------
    // 4. DHT11 Ambient Sensors (Paced Every >= 2000 ms)
    // ----------------------------------------------------
    if (now - xLastDHTTick >= pdMS_TO_TICKS(2000) || xLastDHTTick == 0) {
      xLastDHTTick = now;
      float tVal = dhtN2.readTemperature();
      float hVal = dhtN2.readHumidity();

      if (!isnan(tVal)) {
        localSnap.at = tVal;
        localSnap.atValid = true;
      } else {
        localSnap.atValid = false;
      }

      if (!isnan(hVal)) {
        localSnap.ah = hVal;
        localSnap.ahValid = true;
      } else {
        localSnap.ahValid = false;
      }
    }

    // Commit updated state to global thread-safe store
    if (xSemaphoreTake(xSensorsMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
      g_n2Sensors = localSnap;
      xSemaphoreGive(xSensorsMutex);
    }
  }
}
