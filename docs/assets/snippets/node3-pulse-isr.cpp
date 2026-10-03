// Interrupt Pulse Counter
static volatile uint32_t g_pulseCount = 0;
static portMUX_TYPE g_pulseMux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR pulseISR() {
    portENTER_CRITICAL_ISR(&g_pulseMux);
    g_pulseCount++;
    portEXIT_CRITICAL_ISR(&g_pulseMux);
}
