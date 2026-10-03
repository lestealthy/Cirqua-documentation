
uint16_t readADCFiltered(uint8_t pin) {

    uint32_t total = 0;

    // Throw away the first reading after switching channels.
    // This helps reduce channel-to-channel ADC residue.
    analogRead(pin);

    delayMicroseconds(100);

    for (int i = 0; i < ADC_SAMPLES; i++) {

        total += analogRead(pin);

        delayMicroseconds(150);
    }

    return (uint16_t)(total / ADC_SAMPLES);
}
