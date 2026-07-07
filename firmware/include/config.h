#pragma once

#include <cstdint>

// Control loop timing.
constexpr uint32_t CONTROL_LOOP_HZ = 50;
constexpr uint32_t CONTROL_LOOP_PERIOD_MS = 1000 / CONTROL_LOOP_HZ;
constexpr uint32_t WATCHDOG_TIMEOUT_MS = 500;
constexpr uint32_t SERIAL_BAUD = 115200;

// Joint indices, matching the arm's J0-J5 naming.
enum JointIndex : uint8_t {
    JOINT_BASE = 0,        // J0 — NEMA-17, 15:1 belt
    JOINT_SHOULDER = 1,    // J1 — 2x NEMA-23, 10:1 planetary + 3.33:1 belt (~33.33:1), driven in tandem
    JOINT_ELBOW = 2,       // J2 — NEMA-17, 5:1 gearbox
    JOINT_WRIST_PITCH = 3, // J3 — NEMA-17, 27:1 gearbox
    JOINT_WRIST_ROLL = 4,  // J4 — hobby servo, 35 kg*cm
    JOINT_GRIPPER = 5,     // J5 — hobby servo, MG996R-class
    NUM_JOINTS = 6,
};

// Stepper motor spec. Assumes standard 1.8 deg/step (200 steps/rev) NEMA
// motors and 1/16 microstepping on the drivers — confirm against the
// actual driver DIP-switch/UART configuration once hardware is wired.
constexpr float MOTOR_STEPS_PER_REV = 200.0f;
constexpr uint16_t MICROSTEPS = 16;
constexpr float MICROSTEPS_PER_REV = MOTOR_STEPS_PER_REV * MICROSTEPS;

struct StepperJointConfig {
    uint8_t stepPin;
    uint8_t dirPin;
    float gearRatio;          // motor revolutions per one output-shaft revolution
    float maxSpeedDegPerSec;
    float maxAccelDegPerSec2;
};

// STEP/DIR pins below are placeholders pending final wiring — safe generic
// ESP32-S3-DevKitC-1 GPIOs, avoiding strapping pins (0, 3, 45, 46), the
// octal PSRAM/flash range (26-32) some S3 boards reserve, and the I2C pins
// used for the encoder bus below. Revisit once the driver boards are wired
// and update docs/decisions.md if they change.
constexpr uint8_t STEPPER_ENABLE_PIN = 8; // shared across all 4 driver boards; active LOW

constexpr StepperJointConfig STEPPER_JOINTS[4] = {
    /* JOINT_BASE        */ {4,  15, 15.0f,   60.0f, 90.0f},
    /* JOINT_SHOULDER    */ {5,  16, 33.33f,  40.0f, 60.0f},
    /* JOINT_ELBOW       */ {6,  17, 5.0f,    90.0f, 120.0f},
    /* JOINT_WRIST_PITCH */ {7,  18, 27.0f,   60.0f, 90.0f},
};

// Position feedback: one AS5600 magnetic encoder on every joint except the
// gripper (J0-J4 — the 4 steppers plus the wrist-roll servo), mounted on each
// joint's output shaft (post-gearbox for steppers) — so encoder degrees are
// output-shaft degrees directly, no gear ratio math needed. The AS5600 has a
// fixed I2C address (0x36), so all 5 share one bus through a TCA9548A
// multiplexer, one mux channel per joint. The wrist-roll servo has its own
// internal potentiometer, but it isn't exposed over the servo's control wire
// — the external AS5600 is what actually gets reported for that joint.
constexpr uint8_t I2C_SDA_PIN = 11;
constexpr uint8_t I2C_SCL_PIN = 12;
constexpr uint8_t TCA9548A_ADDR = 0x70;
constexpr uint8_t AS5600_ADDR = 0x36;
constexpr uint8_t NUM_ENCODERS = 5; // JOINT_BASE..JOINT_WRIST_ROLL; JOINT_GRIPPER has none

struct EncoderConfig {
    uint8_t muxChannel;
    float zeroOffsetDeg; // raw AS5600 reading at the joint's defined zero position — calibrate later
};

constexpr EncoderConfig JOINT_ENCODERS[NUM_ENCODERS] = {
    /* JOINT_BASE        */ {0, 0.0f},
    /* JOINT_SHOULDER    */ {1, 0.0f},
    /* JOINT_ELBOW       */ {2, 0.0f},
    /* JOINT_WRIST_PITCH */ {3, 0.0f},
    /* JOINT_WRIST_ROLL  */ {4, 0.0f},
};

struct ServoJointConfig {
    uint8_t pin;
    float minDeg;
    float maxDeg;
    uint16_t minPulseUs;
    uint16_t maxPulseUs;
};

// Wrist roll and gripper — standard hobby-servo PWM range. Adjust min/max
// degrees once the physical range of motion is measured on the real joint.
constexpr ServoJointConfig SERVO_JOINTS[2] = {
    /* JOINT_WRIST_ROLL (index 0 -> JOINT_WRIST_ROLL) */ {9,  0.0f, 180.0f, 500, 2500},
    /* JOINT_GRIPPER    (index 1 -> JOINT_GRIPPER)    */ {10, 0.0f, 180.0f, 500, 2500},
};
