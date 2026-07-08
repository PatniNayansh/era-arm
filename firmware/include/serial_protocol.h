#pragma once

#include <cstddef>
#include <cstdint>

#include "config.h"

// Line protocol over USB serial, matching the driver layer (era_arm/driver):
//
//   Host -> MCU:  "P,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>\n"   target angles, degrees
//   MCU  -> Host: "S,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>,<millis>,<watchdog>\n"
//
// watchdog is 1 if no valid "P" command has arrived within WATCHDOG_TIMEOUT_MS.
class SerialProtocol {
public:
    void begin(uint32_t baud);

    // Non-blocking. Returns true exactly once a full "P,..." line has been
    // received and parsed; fills targetsDeg[NUM_JOINTS] on success.
    bool pollCommand(float targetsDeg[NUM_JOINTS]);

    void writeStatus(const float currentDeg[NUM_JOINTS], uint32_t timestampMs, bool watchdogTripped);

private:
    static constexpr size_t BUF_SIZE = 128;
    char buf_[BUF_SIZE];
    size_t bufLen_ = 0;
};
