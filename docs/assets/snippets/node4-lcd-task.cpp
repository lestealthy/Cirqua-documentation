
void Task_LCD_Node4(void *pvParameters) {

    Wire.begin(
        PIN_N4_LCD_SDA,
        PIN_N4_LCD_SCL
    );

    lcdN4.begin(16, 4);

    lcdN4.backlight();

    TickType_t xLastWakeTime =
        xTaskGetTickCount();

    const TickType_t xFrequency =
        pdMS_TO_TICKS(500);

    for (;;) {

        vTaskDelayUntil(
            &xLastWakeTime,
            xFrequency
        );

        LocalNode4Data n4Snap = {0};

        if (
            xSemaphoreTake(
                xLocalN4Mutex,
                pdMS_TO_TICKS(20)
            ) == pdTRUE
        ) {

            n4Snap = g_localN4;

            xSemaphoreGive(
                xLocalN4Mutex
            );
        }

        lcdSetRow(0);

        lcdN4.printf(
            "EV:%dL pH:%.1f   ",
            n4Snap.tcVolume,
            n4Snap.ph
        );

        lcdSetRow(1);

        lcdN4.printf(
            "TU:%d EC:%duS     ",
            (int)n4Snap.ntu,
            (int)n4Snap.ec
        );

        lcdSetRow(2);

        lcdN4.printf(
            "ST:%.1fC AT:%.1fC  ",
            n4Snap.subTemp,
            n4Snap.ambTemp
        );

        lcdSetRow(3);

        lcdN4.printf(
            "AH:%.0f%%         ",
            n4Snap.ambHum
        );
    }
}
