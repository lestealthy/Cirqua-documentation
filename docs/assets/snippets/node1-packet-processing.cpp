
void processNode2Packet(const String& packet) {
    String doVal      = getFieldFromFrame(packet, "DO");
    String tempVal    = getFieldFromFrame(packet, "Temp");
    String volumeVal  = getFieldFromFrame(packet, "TBV");
    String atVal      = getFieldFromFrame(packet, "AT");
    String ahVal      = getFieldFromFrame(packet, "AH");
    String n2Status   = getFieldFromFrame(packet, "node2");

    if (xSemaphoreTake(xNode2DataMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
        if (doVal.length() > 0)     g_node2Data.doVal       = doVal.toFloat();
        if (tempVal.length() > 0)   g_node2Data.waterTemp   = tempVal.toFloat();
        if (volumeVal.length() > 0) g_node2Data.volume      = volumeVal.toInt();
        if (atVal.length() > 0)     g_node2Data.ambientTemp = atVal.toFloat();
        if (ahVal.length() > 0)     g_node2Data.humidity    = ahVal.toFloat();
        if (n2Status.length() > 0)  g_node2Data.node2Health = (n2Status.toInt() == 1);

        if (doVal.length() > 0 && tempVal.length() > 0 && volumeVal.length() > 0 &&
            atVal.length() > 0 && ahVal.length() > 0 && n2Status.length() > 0) {
            g_node2Data.packetValid = true;
            g_lastNode2Rx = millis();
        }
        xSemaphoreGive(xNode2DataMutex);
    }
}
