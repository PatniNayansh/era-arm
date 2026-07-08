#include "as5600_encoder.h"

#include <Wire.h>

#include "config.h"

namespace {
void selectMuxChannel(uint8_t channel) {
    Wire.beginTransmission(TCA9548A_ADDR);
    Wire.write(static_cast<uint8_t>(1u << channel));
    Wire.endTransmission();
}
} // namespace

void As5600Encoder::begin(uint8_t muxChannel, float zeroOffsetDeg) {
    muxChannel_ = muxChannel;
    zeroOffsetDeg_ = zeroOffsetDeg;
}

float As5600Encoder::readDeg() {
    selectMuxChannel(muxChannel_);

    Wire.beginTransmission(AS5600_ADDR);
    Wire.write(0x0C); // RAW_ANGLE high byte
    bool ok = (Wire.endTransmission(false) == 0);

    if (ok) {
        Wire.requestFrom(static_cast<int>(AS5600_ADDR), 2);
        ok = Wire.available() >= 2;
    }

    if (ok) {
        uint8_t hi = Wire.read();
        uint8_t lo = Wire.read();
        uint16_t raw = ((static_cast<uint16_t>(hi) << 8) | lo) & 0x0FFFu;

        float deg = (raw * 360.0f) / 4096.0f - zeroOffsetDeg_;
        while (deg < 0.0f) deg += 360.0f;
        while (deg >= 360.0f) deg -= 360.0f;
        lastDeg_ = deg;
    }

    lastReadOk_ = ok;
    return lastDeg_;
}
