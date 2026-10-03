
String cleanUpstreamPacket(String rawPacket) {

    String cleaned = "";

    int startIdx = 0;

    while (true) {

        int pipeIdx =
            rawPacket.indexOf(
                '|',
                startIdx
            );

        String token = "";

        if (pipeIdx == -1) {

            token =
                rawPacket.substring(
                    startIdx
                );

        } else {

            token =
                rawPacket.substring(
                    startIdx,
                    pipeIdx
                );
        }

        if (
            !token.startsWith("AT:") &&
            !token.startsWith("AH:")
        ) {

            if (cleaned.length() > 0) {
                cleaned += "|";
            }

            cleaned += token;
        }

        if (pipeIdx == -1) {
            break;
        }

        startIdx =
            pipeIdx + 1;
    }

    return cleaned;
}
