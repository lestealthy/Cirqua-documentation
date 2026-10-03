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
