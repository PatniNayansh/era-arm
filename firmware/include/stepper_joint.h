#pragma once

#include <AccelStepper.h>

#include "config.h"

// Wraps one AccelStepper instance and converts target output-shaft degrees
// (the unit used over serial) to motor microsteps (the unit AccelStepper
// moves in), given the joint's gear ratio. Drives motion open-loop — actual
// position is read back from an AS5600Encoder, not from here.
class StepperJoint {
public:
    void begin(const StepperJointConfig &cfg);

    void setTargetDeg(float deg);

    // Must be called as often as possible (every loop() iteration) to
    // generate a smooth step pulse train — do not throttle this to 50 Hz.
    void run();

private:
    AccelStepper stepper_{AccelStepper::DRIVER, 0, 0};
    float gearRatio_ = 1.0f;
    float stepsPerOutputDeg_ = 1.0f;
};
