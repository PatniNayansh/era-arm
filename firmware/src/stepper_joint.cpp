#include "stepper_joint.h"

void StepperJoint::begin(const StepperJointConfig &cfg) {
    gearRatio_ = cfg.gearRatio;
    stepsPerOutputDeg_ = (MICROSTEPS_PER_REV * gearRatio_) / 360.0f;

    stepper_ = AccelStepper(AccelStepper::DRIVER, cfg.stepPin, cfg.dirPin);
    stepper_.setMaxSpeed(cfg.maxSpeedDegPerSec * stepsPerOutputDeg_);
    stepper_.setAcceleration(cfg.maxAccelDegPerSec2 * stepsPerOutputDeg_);
}

void StepperJoint::setTargetDeg(float deg) {
    stepper_.moveTo(static_cast<long>(deg * stepsPerOutputDeg_));
}

void StepperJoint::run() {
    stepper_.run();
}
