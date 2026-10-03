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
