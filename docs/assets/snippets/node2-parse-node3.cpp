
bool parseNode3ReversePacket(const char* frame, Node3ReverseTelemetry& outN3) {
  if (!frame) return false;
  const char* pFR = strstr(frame, "|FR:");
  const char* pNode3 = strstr(frame, "|node3:");
  if (!pFR || !pNode3) return false;

  int n3Status = 0;
  if (sscanf(pFR, "|FR:%f", &outN3.fr) != 1) return false;
  if (sscanf(pNode3, "|node3:%d", &n3Status) != 1) return false;

  outN3.node3Status = (n3Status == 1);
  outN3.isValid = true;
  return true;
}
