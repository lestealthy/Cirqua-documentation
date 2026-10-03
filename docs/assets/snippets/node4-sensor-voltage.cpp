
float readSensorVoltage(uint8_t pin) {

    uint32_t totalMv = 0;

    // Discard first sample after ADC channel switching.
    analogRead(pin);
    delayMicroseconds(100);

    for (int i = 0; i < ADC_SAMPLES; i++) {

        totalMv += analogReadMilliVolts(pin);

        delayMicroseconds(150);
    }

    float voltage =
        ((float)totalMv / ADC_SAMPLES) / 1000.0f;

    return voltage;
}
