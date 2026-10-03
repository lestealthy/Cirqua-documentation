
void handleSerialCalibrationCommands() {

    if (Serial.available() > 0) {

        String cmd =
            Serial.readStringUntil('\n');

        cmd.trim();

        if (cmd.equalsIgnoreCase("HELP")) {

            Serial.println(
                "\n========== NODE 4 CALIBRATION DEBUG CONSOLE =========="
            );

            Serial.println(
                "STATUS        - View current raw ADC and calculated values"
            );

            Serial.println(
                "SET:EC_K=<val>- Set and save EC K factor"
            );

            Serial.println(
                "SET:PH_S=<val>- Set and save pH slope"
            );

            Serial.println(
                "SET:PH_O=<val>- Set and save pH offset"
            );

            Serial.println(
                "RESET         - Reset calibration to factory defaults"
            );

            Serial.println(
                "=====================================================\n"
            );
        }

        // ====================================================
        // STATUS
        // ====================================================

        else if (cmd.equalsIgnoreCase("STATUS")) {

            uint16_t phRaw =
                readADCFiltered(PIN_PH_ANALOG);

            uint16_t ecRaw =
                readADCFiltered(PIN_EC_ANALOG);

            uint16_t turbRaw =
                readADCFiltered(PIN_TURB_ANALOG);

            float phVoltage =
                readSensorVoltage(PIN_PH_ANALOG);

            float ecVoltage =
                readSensorVoltage(PIN_EC_ANALOG);

            float turbVoltage =
                readSensorVoltage(PIN_TURB_ANALOG);

            Serial.println(
                "\n--- Live Raw Sensor Diagnostics ---"
            );

            Serial.printf(
                "pH   -> Raw ADC: %4d | Voltage: %.3fV\n",
                phRaw,
                phVoltage
            );

            Serial.printf(
                "EC   -> Raw ADC: %4d | Voltage: %.3fV | K: %.3f\n",
                ecRaw,
                ecVoltage,
                calData.ecKFactor
            );

            Serial.printf(
                "Turb -> Raw ADC: %4d | Voltage: %.3fV\n",
                turbRaw,
                turbVoltage
            );

            Serial.printf(
                "Saved Constants -> pH Slope: %.3f | pH Offset: %.3f | EC K: %.3f\n\n",
                calData.phSlope,
                calData.phOffset,
                calData.ecKFactor
            );
        }

        // ====================================================
        // EC K
        // ====================================================

        else if (cmd.startsWith("SET:EC_K=")) {

            float val =
                cmd.substring(9).toFloat();

            if (val > 0.0f) {

                calData.ecKFactor = val;

                preferences.begin(
                    "node4_cal",
                    false
                );

                preferences.putFloat(
                    "ecKFactor",
                    calData.ecKFactor
                );

                preferences.end();

                Serial.printf(
                    "[SUCCESS] EC K-Factor updated and saved to flash: %.3f\n",
                    calData.ecKFactor
                );

            } else {

                Serial.println(
                    "[ERROR] Invalid value for EC K-Factor."
                );
            }
        }

        // ====================================================
        // pH SLOPE
        // ====================================================

        else if (cmd.startsWith("SET:PH_S=")) {

            float val =
                cmd.substring(9).toFloat();

            calData.phSlope = val;

            preferences.begin(
                "node4_cal",
                false
            );

            preferences.putFloat(
                "phSlope",
                calData.phSlope
            );

            preferences.end();

            Serial.printf(
                "[SUCCESS] pH Slope updated and saved: %.3f\n",
                calData.phSlope
            );
        }

        // ====================================================
        // pH OFFSET
        // ====================================================

        else if (cmd.startsWith("SET:PH_O=")) {

            float val =
                cmd.substring(9).toFloat();

            calData.phOffset = val;

            preferences.begin(
                "node4_cal",
                false
            );

            preferences.putFloat(
                "phOffset",
                calData.phOffset
            );

            preferences.end();

            Serial.printf(
                "[SUCCESS] pH Offset updated and saved: %.3f\n",
                calData.phOffset
            );
        }

        // ====================================================
        // RESET
        // ====================================================

        else if (cmd.equalsIgnoreCase("RESET")) {

            preferences.begin(
                "node4_cal",
                false
            );

            preferences.clear();

            preferences.end();

            loadCalibration();

            Serial.println(
                "[SUCCESS] Calibration reset to defaults."
            );
        }
    }
}
