#include <Arduino.h>
#include <Wire.h>

#include "as5600_encoder.h"
#include "config.h"
#include "serial_protocol.h"
#include "servo_joint.h"
#include "stepper_joint.h"

StepperJoint stepperJoints[4];       // JOINT_BASE..JOINT_WRIST_PITCH — open-loop actuation
As5600Encoder encoders[NUM_ENCODERS]; // JOINT_BASE..JOINT_WRIST_ROLL — actual position feedback
ServoJoint servoJoints[2];           // JOINT_WRIST_ROLL, JOINT_GRIPPER
SerialProtocol protocol;

uint32_t lastCommandMillis = 0;
uint32_t lastControlTickMillis = 0;
bool watchdogTripped = false;

void setEnabled(bool enabled) {
    digitalWrite(STEPPER_ENABLE_PIN, enabled ? LOW : HIGH); // active LOW
}

void setup() {
    pinMode(STEPPER_ENABLE_PIN, OUTPUT);
    setEnabled(true);

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

    for (uint8_t i = 0; i < 4; i++) {
        stepperJoints[i].begin(STEPPER_JOINTS[i]);
    }
    for (uint8_t i = 0; i < NUM_ENCODERS; i++) {
        encoders[i].begin(JOINT_ENCODERS[i].muxChannel, JOINT_ENCODERS[i].zeroOffsetDeg);
    }
    for (uint8_t i = 0; i < 2; i++) {
        servoJoints[i].begin(SERVO_JOINTS[i]);
    }

    protocol.begin(SERIAL_BAUD);
    lastCommandMillis = millis();
}

void loop() {
    // Run as fast as possible — AccelStepper needs frequent run() calls to
    // generate a smooth pulse train, independent of the 50 Hz command rate.
    for (auto &joint : stepperJoints) {
        joint.run();
    }

    float targetsDeg[NUM_JOINTS];
    if (protocol.pollCommand(targetsDeg)) {
        lastCommandMillis = millis();
        if (watchdogTripped) {
            watchdogTripped = false;
            setEnabled(true);
        }
        for (uint8_t i = 0; i < 4; i++) {
            stepperJoints[i].setTargetDeg(targetsDeg[i]);
        }
        servoJoints[0].setTargetDeg(targetsDeg[JOINT_WRIST_ROLL]);
        servoJoints[1].setTargetDeg(targetsDeg[JOINT_GRIPPER]);
    }

    uint32_t now = millis();
    if (!watchdogTripped && (now - lastCommandMillis > WATCHDOG_TIMEOUT_MS)) {
        watchdogTripped = true;
        setEnabled(false); // de-energize steppers; servos hold last position
    }

    if (now - lastControlTickMillis >= CONTROL_LOOP_PERIOD_MS) {
        lastControlTickMillis = now;

        float currentDeg[NUM_JOINTS];
        for (uint8_t i = 0; i < NUM_ENCODERS; i++) {
            currentDeg[i] = encoders[i].readDeg(); // covers JOINT_BASE..JOINT_WRIST_ROLL
        }
        currentDeg[JOINT_GRIPPER] = servoJoints[1].currentDeg(); // no encoder — last commanded

        protocol.writeStatus(currentDeg, now, watchdogTripped);
    }
}
