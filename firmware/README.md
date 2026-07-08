# Layer 1 — ESP32 Firmware

PlatformIO (Arduino framework) project targeting ESP32-S3. Drives the arm's 6
joints and talks to the Python driver layer (`era_arm/driver`) over USB serial.

## Hardware (7 physical actuators, 6 logical joints)

| Joint | Actuator | Reduction |
|---|---|---|
| J0 base | 1x NEMA-17 stepper | 15:1 belt |
| J1 shoulder | 2x NEMA-23 stepper (shared STEP/DIR, driven in tandem) | 10:1 planetary + 3.33:1 belt (~33.33:1) |
| J2 elbow | 1x NEMA-17 stepper | 5:1 gearbox |
| J3 wrist pitch | 1x NEMA-17 stepper | 27:1 gearbox |
| J4 wrist roll | 1x hobby servo (35 kg*cm) | direct |
| J5 gripper | 1x hobby servo (MG996R-class) | direct |

Every joint except the gripper (J0-J4: the 4 steppers plus the wrist-roll
servo) has an **AS5600 magnetic encoder** mounted on its output shaft — this is
the actual position source reported over serial, not step counting or the
servo's last commanded angle. Steppers are still *commanded* open-loop (step
pulses via AccelStepper); the encoder only reads back where the joint really
is. The wrist-roll servo has its own internal potentiometer, but it isn't
exposed over the servo's control wire, so the external AS5600 is what actually
gets reported for that joint too. The AS5600 has a fixed I2C address (0x36),
so all 5 encoders share one I2C bus through a TCA9548A multiplexer, one mux
channel per joint. The gripper (J5) has no encoder — its status is just its
last commanded angle.

## Structure

- `include/config.h` — pin assignments, gear ratios, encoder mux channels,
  timing constants. **Pin numbers and encoder zero-offsets are placeholders**
  pending final wiring/calibration — update here once the driver boards and
  encoders are wired, and note any change in `docs/decisions.md`.
- `include/stepper_joint.h` / `src/stepper_joint.cpp` — wraps one
  [AccelStepper](https://github.com/waspinator/AccelStepper) instance,
  converting target output-shaft degrees to motor microsteps via the joint's
  gear ratio. Drives motion only — does not report position.
- `include/as5600_encoder.h` / `src/as5600_encoder.cpp` — reads one AS5600
  encoder through its TCA9548A mux channel; this is the reported position for
  every joint except the gripper.
- `include/servo_joint.h` / `src/servo_joint.cpp` — wraps one
  [ESP32Servo](https://github.com/madhephaestus/ESP32Servo) instance.
- `include/serial_protocol.h` / `src/serial_protocol.cpp` — parses incoming
  position commands and writes status lines (protocol below).
- `src/main.cpp` — 50 Hz control loop + 500 ms command watchdog.

## Serial protocol

```
Host -> MCU:  P,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>\n     target angles, degrees
MCU  -> Host: S,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>,<millis>,<watchdog>\n
```

`watchdog` is `1` if no valid `P` command has arrived in the last 500 ms — the
firmware de-energizes the stepper drivers (shared enable pin) until a new
command arrives. Servos hold their last commanded position (they can't be
de-powered individually without extra hardware).

Baud rate: 115200.

## Build

```
uv tool install platformio   # one-time
pio run                      # compile
pio run -t upload            # flash (once hardware is connected)
pio device monitor            # watch status lines at 115200 baud
```

Status: initial scaffold written and compiling for `esp32-s3-devkitc-1`.
Not yet flashed or tested on real hardware — pins, gear ratios, and encoder
zero-offsets need verification/calibration once the arm is physically wired.
