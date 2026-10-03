// Frame Integrity Check
bool validateUpstreamFrame(const char* frame) {
    if (!frame) return false;
    return (strstr(frame, "TAV:") || strstr(frame, "|TAV:")) &&
           strstr(frame, "|node1:") &&
           strstr(frame, "|DO:")   &&
           strstr(frame, "|node2:");
}
