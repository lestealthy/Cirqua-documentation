// Helper to send generic emails asynchronously/safely
bool sendMailMessage(const String& subject, const String& htmlMsg) {
    if (WiFi.status() != WL_CONNECTED) return false;

    ESP_Mail_Session session;
    session.server.host_name = SMTP_HOST;
    session.server.port = SMTP_PORT;
    session.login.email = AUTHOR_EMAIL;
    session.login.password = AUTHOR_PASSWORD;
    session.sec.type = esp_mail_secure_transport_ssl;

    SMTP_Message message;
    message.sender.name = "WattLab Node 4";
    message.sender.email = AUTHOR_EMAIL;
    message.subject = subject.c_str();
    message.addRecipient("Operator", RECIPIENT_EMAIL);
    message.html.content = htmlMsg.c_str();
    message.html.transfer_encoding = enc_base64;
    message.priority = esp_mail_priority_high;

    if (!smtp.connect(&session)) {
        Serial.printf("[SMTP ERROR] Connect failed: %s\n", smtp.errorReason().c_str());
        return false;
    }

    bool success = MailClient.sendMail(&smtp, &message);
    if (success) {
        Serial.println("[SMTP SUCCESS] Email sent successfully!");
    } else {
        Serial.printf("[SMTP ERROR] Send failed: %s\n", smtp.errorReason().c_str());
    }
    smtp.closeSession();
    return success;
}
