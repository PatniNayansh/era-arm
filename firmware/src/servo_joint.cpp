#include "servo_joint.h"

void ServoJoint::begin(const ServoJointConfig &cfg) {
    cfg_ = cfg;
    servo_.setPeriodHertz(50);
    servo_.attach(cfg_.pin, cfg_.minPulseUs, cfg_.maxPulseUs);
    setTargetDeg((cfg_.minDeg + cfg_.maxDeg) / 2.0f);
}

void ServoJoint::setTargetDeg(float deg) {
    if (deg < cfg_.minDeg) {
        deg = cfg_.minDeg;
    } else if (deg > cfg_.maxDeg) {
        deg = cfg_.maxDeg;
    }
    currentDeg_ = deg;
    servo_.write(static_cast<int>(currentDeg_));
}
