// Initialize Wi-Fi and Synchronize NTP Time for Tunis (UTC+1)
void initNetworkAndTime() {
    Serial.printf("Connecting to Wi-Fi: %s\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[INFO] Wi-Fi Connected!");
        // Configure Tunis Time (UTC+1 = 3600 seconds offset, 0 daylight saving)
        configTime(3600, 0, "pool.ntp.org", "time.nist.gov");
        Serial.println("[INFO] Synchronizing NTP time for Tunis...");
        
        time_t nowSecs = time(nullptr);
        int retry = 0;
        while (nowSecs < 1700000000 && retry < 15) { // Ensure epoch is past valid threshold
            delay(1000);
            nowSecs = time(nullptr);
            retry++;
        }
        Serial.printf("[INFO] Current Epoch Time: %lu\n", (unsigned long)nowSecs);
    } else {
        Serial.println("\n[ERROR] Wi-Fi Connection Failed!");
    }
}
