#pragma once

#include <ESP32Servo.h>

#include "config.h"

// Wraps one hobby servo. Hobby servos have no position feedback pin, so
// currentDeg() reports the last commanded angle, not a measured one.
class ServoJoint {
public:
    void begin(const ServoJointConfig &cfg);

    void setTargetDeg(float deg);
    float currentDeg() const { return currentDeg_; }

private:
    Servo servo_;
    ServoJointConfig cfg_{};
    float currentDeg_ = 0.0f;
};
