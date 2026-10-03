
void Task_Sensors_Node4(void *pvParameters) {

    configureADC();

    initializeDS18B20();

    initializeDHT();

    pinMode(PIN_EFFLUENT_TRIG, OUTPUT);
    pinMode(PIN_EFFLUENT_ECHO, INPUT);

    digitalWrite(
        PIN_EFFLUENT_TRIG,
        LOW
    );

    TickType_t xLastWakeTime =
        xTaskGetTickCount();

    const TickType_t xFrequency =
        pdMS_TO_TICKS(1000);

    TickType_t xLastDHTTick = 0;

    for (;;) {

        vTaskDelayUntil(
            &xLastWakeTime,
            xFrequency
        );

        TickType_t now =
            xTaskGetTickCount();

        LocalNode4Data localSnap;

        // ----------------------------------------------------
        // COPY CURRENT DATA
        // ----------------------------------------------------

        if (xSemaphoreTake(
                xLocalN4Mutex,
                pdMS_TO_TICKS(50)
            ) == pdTRUE) {

            localSnap = g_localN4;

            xSemaphoreGive(
                xLocalN4Mutex
            );
        }

        // ====================================================
        // 1. DS18B20 SUBMERGED TEMPERATURE
        // ====================================================

        float st = DEVICE_DISCONNECTED_C;

        if (sensorsN4.getDeviceCount() > 0) {

            sensorsN4.requestTemperatures();

            st =
                sensorsN4.getTempCByIndex(0);
        }

        if (st != DEVICE_DISCONNECTED_C &&
            st >= -55.0f &&
            st <= 125.0f) {

            localSnap.subTemp = st;
            localSnap.subTempValid = true;

        } else {

            localSnap.subTempValid = false;
        }

        float validTempForComp =
            localSnap.subTempValid
            ? localSnap.subTemp
            : 25.0f;

        // ====================================================
        // 2. pH SENSOR
        // ====================================================

        uint16_t phRaw =
            readADCFiltered(PIN_PH_ANALOG);

        float phVolt =
            readSensorVoltage(PIN_PH_ANALOG);

        /*
           Existing calibration model preserved:

               pHcalculated =
                   slope * voltage + offset

           Temperature compensation also preserved.
        */

        float phCompensationCoefficient =
            1.0f +
            0.02f *
            (validTempForComp - 25.0f);

        float calculatedPh =
            (calData.phSlope * phVolt) +
            calData.phOffset;

        float finalPh =
            7.0f +
            ((calculatedPh - 7.0f) /
             phCompensationCoefficient);

        /*
           Basic sanity check.

           A completely saturated / disconnected ADC signal
           should not be reported as a valid pH measurement.
        */

        if (phVolt >= 0.02f &&
            phVolt <= 3.30f &&
            finalPh >= 0.0f &&
            finalPh <= 14.0f) {

            localSnap.ph = finalPh;
            localSnap.phValid = true;

        } else {

            localSnap.phValid = false;
        }

        // ====================================================
        // 3. TURBIDITY
        // ====================================================

        uint16_t turbRaw =
            readADCFiltered(PIN_TURB_ANALOG);

        float turbVolt =
            readSensorVoltage(PIN_TURB_ANALOG);

        float ntu = 0.0f;

        /*
           SEN0189 / DFRobot turbidity relationship.

           IMPORTANT:
           The original code used 5.0 V as the ADC reference.
           That is incorrect for the ESP32 ADC measurement.

           The voltage here is the actual voltage measured at
           the ESP32 ADC input.
        */

        if (turbVolt >= 3.20f) {

            // Very clear water / sensor output near upper range
            ntu = 0.0f;

        }
        else if (turbVolt <= 0.50f) {

            // Extremely turbid / below useful formula range
            ntu = 3000.0f;

        }
        else {

            ntu =
                -1120.4f *
                (turbVolt * turbVolt)

                + 5742.3f *
                turbVolt

                - 4353.8f;

            if (ntu < 0.0f) {
                ntu = 0.0f;
            }

            if (ntu > 3000.0f) {
                ntu = 3000.0f;
            }
        }

        /*
           Don't automatically invalidate the turbidity sensor
           just because it is reading near one end of its range.

           Saturation is a valid physical condition.
        */

        if (turbVolt >= 0.0f &&
            turbVolt <= 3.30f) {

            localSnap.ntu = ntu;
            localSnap.ntuValid = true;

        } else {

            localSnap.ntuValid = false;
        }

        // ====================================================
        // 4. EC SENSOR
        // ====================================================

        uint16_t ecRaw =
            readADCFiltered(PIN_EC_ANALOG);

        float ecVolt =
            readSensorVoltage(PIN_EC_ANALOG);

        /*
           Existing K-factor behavior preserved.

           Original:
               EC(mS/cm) = voltage * K

           Then temperature compensation and conversion to uS/cm.
        */

        float ecCoefficient =
            1.0f +
            0.0185f *
            (validTempForComp - 25.0f);

        float rawEcMilliSiemens =
            ecVolt * calData.ecKFactor;

        float compensatedEc =
            (rawEcMilliSiemens /
             ecCoefficient) *
            1000.0f;

        if (compensatedEc < 0.0f) {
            compensatedEc = 0.0f;
        }

        /*
           Reject impossible ADC conditions but do not reject
           a zero EC value — zero/very-low conductivity is a
           legitimate measurement.
        */

        if (ecVolt >= 0.0f &&
            ecVolt <= 3.30f) {

            localSnap.ec = compensatedEc;
            localSnap.ecValid = true;

        } else {

            localSnap.ecValid = false;
        }

        // ====================================================
        // 5. DHT11
        // ====================================================

        if (
            xLastDHTTick == 0 ||
            now - xLastDHTTick >=
            pdMS_TO_TICKS(2000)
        ) {

            xLastDHTTick = now;

            float at =
                dhtN4.readTemperature();

            float ah =
                dhtN4.readHumidity();

            if (!isnan(at) &&
                at >= -20.0f &&
                at <= 80.0f) {

                localSnap.ambTemp = at;
                localSnap.ambTempValid = true;

            } else {

                localSnap.ambTempValid = false;
            }

            if (!isnan(ah) &&
                ah >= 0.0f &&
                ah <= 100.0f) {

                localSnap.ambHum = ah;
                localSnap.ambHumValid = true;

            } else {

                localSnap.ambHumValid = false;
            }
        }

        // ====================================================
        // 6. HC-SR04 TANK VOLUME
        // ====================================================

        int tankVolume = 0;

        if (readTankVolume(tankVolume)) {

            localSnap.tcVolume = tankVolume;
            localSnap.tcValid = true;

        } else {

            localSnap.tcValid = false;
        }

        // ====================================================
        // STORE SENSOR SNAPSHOT
        // ====================================================

        if (xSemaphoreTake(
                xLocalN4Mutex,
                pdMS_TO_TICKS(50)
            ) == pdTRUE) {

            g_localN4 = localSnap;

            xSemaphoreGive(
                xLocalN4Mutex
            );
        }
    }
}
