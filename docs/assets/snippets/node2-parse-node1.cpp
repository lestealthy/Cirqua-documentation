
bool parseNode1Packet(const char* frame, Node1Telemetry& outN1) {
  if (!frame) return false;
  const char* pTAV = strstr(frame, "|TAV:");
  const char* pNode1 = strstr(frame, "|node1:");
  if (!pTAV || !pNode1) return false;

  int n1Status = 0;
  if (sscanf(pTAV, "|TAV:%f", &outN1.tav) != 1) return false;
  if (sscanf(pNode1, "|node1:%d", &n1Status) != 1) return false;

  outN1.node1Status = (n1Status == 1);
  outN1.isValid = true;
  return true;
}
