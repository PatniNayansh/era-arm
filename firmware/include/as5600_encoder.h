#pragma once

#include <cstdint>

// Reads one AS5600 magnetic encoder behind a TCA9548A I2C mux channel.
// This is the source of truth for a joint's actual position — steppers are
// still commanded open-loop (step pulses), but reported/verified position
// comes from here, not from counting steps.
class As5600Encoder {
public:
    void begin(uint8_t muxChannel, float zeroOffsetDeg);

    // Returns degrees in [0, 360). On I2C failure, returns the last known
    // good reading instead — check lastReadOk() to detect a stale value.
    float readDeg();

    bool lastReadOk() const { return lastReadOk_; }

private:
    uint8_t muxChannel_ = 0;
    float zeroOffsetDeg_ = 0.0f;
    float lastDeg_ = 0.0f;
    bool lastReadOk_ = true;
};
