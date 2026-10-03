// ============================================================
String getFieldFromFrame(const String& packet, const String& fieldName) {
    String search = "|" + fieldName + ":";
    int start = packet.indexOf(search);
    if (start < 0) return "";

    start += search.length();
    int end = packet.indexOf("|", start);
    if (end < 0) end = packet.indexOf(";", start);
    if (end < 0) end = packet.length();

    return packet.substring(start, end);
}
