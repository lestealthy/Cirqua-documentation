
void configureADC() {

    pinMode(PIN_PH_ANALOG, INPUT);
    pinMode(PIN_TURB_ANALOG, INPUT);
    pinMode(PIN_EC_ANALOG, INPUT);

    analogSetPinAttenuation(
        PIN_PH_ANALOG,
        SENSOR_ADC_ATTENUATION
    );

    analogSetPinAttenuation(
        PIN_TURB_ANALOG,
        SENSOR_ADC_ATTENUATION
    );

    analogSetPinAttenuation(
        PIN_EC_ANALOG,
        SENSOR_ADC_ATTENUATION
    );

    // 12-bit ADC
    analogReadResolution(12);

    Serial.println("[ADC] Resolution: 12-bit");
    Serial.println("[ADC] Attenuation: 11 dB");
    Serial.println("[ADC] Multi-sample filtering enabled");
}
