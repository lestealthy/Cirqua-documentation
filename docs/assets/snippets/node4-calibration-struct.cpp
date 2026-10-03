
// ============================================================
// NON-VOLATILE STORAGE
// ============================================================

Preferences preferences;

struct CalibrationData {
    float phSlope;
    float phOffset;
    float ecKFactor;
};

static CalibrationData calData;
