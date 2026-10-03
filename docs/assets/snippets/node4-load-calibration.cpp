
void loadCalibration() {

    preferences.begin("node4_cal", false);

    calData.phSlope =
        preferences.getFloat("phSlope", 3.5f);

    calData.phOffset =
        preferences.getFloat("phOffset", -1.75f);

    calData.ecKFactor =
        preferences.getFloat("ecKFactor", 9.997f);

    preferences.end();

    Serial.println("--- Loaded Calibration Constants ---");

    Serial.printf(
        "pH Slope: %.3f | pH Offset: %.3f | EC K-Factor: %.3f\n",
        calData.phSlope,
        calData.phOffset,
        calData.ecKFactor
    );
}
