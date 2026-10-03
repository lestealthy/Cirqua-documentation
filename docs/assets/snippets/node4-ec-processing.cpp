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
