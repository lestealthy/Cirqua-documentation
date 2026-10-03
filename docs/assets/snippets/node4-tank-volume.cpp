
bool readTankVolume(int &volumeLiters) {

    digitalWrite(PIN_EFFLUENT_TRIG, LOW);
    delayMicroseconds(3);

    digitalWrite(PIN_EFFLUENT_TRIG, HIGH);
    delayMicroseconds(10);

    digitalWrite(PIN_EFFLUENT_TRIG, LOW);

    long duration =
        pulseIn(
            PIN_EFFLUENT_ECHO,
            HIGH,
            25000
        );

    if (duration <= 0) {
        return false;
    }

    float distance =
        duration * 0.0343f / 2.0f;

    // Reject physically impossible measurements
    if (distance < 0.0f ||
        distance > TANK_HEIGHT + 20.0f) {
        return false;
    }

    float waterHeight =
        TANK_HEIGHT - distance;

    if (waterHeight < 0.0f) {
        waterHeight = 0.0f;
    }

    if (waterHeight > TANK_HEIGHT) {
        waterHeight = TANK_HEIGHT;
    }

    float volume =
        (3.14159f *
         TANK_RADIUS *
         TANK_RADIUS *
         waterHeight) / 1000.0f;

    if (volume < 0.0f) {
        volume = 0.0f;
    }

    volumeLiters = (int)volume;

    return true;
}
