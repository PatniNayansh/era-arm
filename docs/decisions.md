# Decision Log

Format: what we decided, why, and when to revisit.

## Ubuntu 24.04 LTS (not 22.04 or 26.04)
22.04 too old for the RTX 5070 (Blackwell/sm_120) stack; 26.04 too new (ecosystem
not caught up). 24.04 = mature, ships Python 3.12 natively, and every RTX-50 guide
targets it. Both machines standardized on it.

## Python 3.12 (not 3.14)
PyTorch has no CUDA wheels for 3.14 yet (installs CPU-only), and LeRobot targets
3.12/3.13. Pinned via uv so the system Python version is irrelevant.

## ffmpeg 7 with libsvtav1 (not 8)
LeRobot's dataset format encodes video with libsvtav1; ffmpeg 8 can be too new for
the TorchCodec decoder. 7.x is the known-good version.

## WSL2 now, dual-boot native Ubuntu by ~month 2
WSL2 is fine for env setup + firmware/serial, but can't do USB cameras without
recompiling the kernel. Native Ubuntu needed before the camera/teleop phase.

## Models: ACT → SmolVLA → GR00T-N1.5 (primary) → GR00T-N1.7 (stretch)
ACT is the mandatory baseline + month-3 gate (must hit >=40% before any VLA work).
GR00T-N1.5 primary for best documented results on cheap arms. Settled — not revisiting.

## uv for environment management
Pins the project's own Python + dependencies, isolated from the system.

## Flat package layout (era_arm/ at repo root, not src/era_arm/)
`uv init --package` defaults to a src-layout. We want era_arm/ at the repo root so
it visibly matches the six-layer architecture in the tree. Fixed by moving the
package up and setting `module-root = ""` under `[tool.uv.build-backend]` in
pyproject.toml so uv's build backend looks at the repo root instead of src/.

## PlatformIO installed as a uv tool, not via pip/apt
No system pip was available and apt needs sudo (unusable in this shell). `uv tool
install platformio` works standalone, but PlatformIO internally shells out to pip
to fetch esptool — had to `ensurepip` inside PlatformIO's own uv-managed venv once
to unblock that. One-time fix; `pio` works normally after.

## Position feedback: AS5600 magnetic encoders, not step counting
Corrected an earlier wrong assumption that the steppers were open-loop with no
encoders. Every joint except the gripper (J0-J4: the 4 steppers plus the
wrist-roll servo) actually has an AS5600 magnetic encoder on its output shaft,
and that's the reported position — not counted microsteps, and not the servo's
last-commanded angle. Motion is still commanded open-loop (step pulses for
steppers, PWM for the wrist-roll servo); encoders only read back actual
position, they don't (yet) feed back into a PID correction loop. Revisit if
slipped-step detection/correction becomes necessary. Initially assumed only
4 encoders (one per stepper); corrected again to 5 once the wrist-roll servo's
encoder was confirmed too — the servo's own internal potentiometer isn't
exposed over its control wire, so the external AS5600 is the only way to get
real position feedback on that joint.

## AS5600 encoders share one I2C bus via a TCA9548A mux
The AS5600 has a fixed I2C address (0x36), so 5 of them can't sit on one bus
directly. Options considered: a mux chip (TCA9548A), bit-banged extra I2C buses
per encoder, or swapping to the address-programmable AS5600L. Went with the mux
— cheap, standard for this exact "N identical fixed-address I2C sensors" problem,
uses only 2 ESP32 GPIOs regardless of encoder count, and doesn't require buying
different encoder chips than what's already on hand. One encoder per joint
(mounted on the joint's output shaft), not one per motor — matters for J1
(shoulder), which has 2 physical motors but one shared output shaft/encoder.

## AccelStepper + ESP32Servo libraries for firmware
Rather than hand-rolling step-pulse timing and PWM generation: AccelStepper handles
non-blocking multi-stepper motion (acceleration, step timing) and is called every
loop() iteration independent of the 50 Hz command rate; ESP32Servo handles hobby
servo PWM via the ESP32's LEDC peripheral. Both are the standard/idiomatic choice
for this combination on ESP32.

## Shoulder joint (J1): two motors, one STEP/DIR signal
J1 has two physical NEMA-23 motors sharing the load. Firmware treats it as one
logical joint — both driver boards are wired in parallel to the same STEP/DIR
GPIO pair, so they move identically without needing separate firmware logic.

## Serial protocol: simple ASCII CSV, not binary
`P,<j0>..<j5>\n` in / `S,<j0>..<j5>,<millis>,<watchdog>\n` out, degrees as the
unit. Chosen for human-debuggability (readable directly in a serial monitor)
during bring-up; the Python driver layer is the only other consumer, so revisit
only if the 50 Hz rate turns out to strain parsing overhead (unlikely at this
message size).

## Layer 2 driver: plain USB webcam via OpenCV (unconfirmed assumption)
No camera hardware was specified yet, so `era_arm/driver/camera.py` defaults to
a generic UVC webcam via `cv2.VideoCapture` — the cheapest, most common choice.
**Revisit this if the arm actually uses a depth camera (e.g. Intel RealSense)**
— that needs a different SDK (`pyrealsense2`), not OpenCV. Nothing above the
driver layer depends on OpenCV specifically, so swapping is a small, contained
change if this guess is wrong.

## Layer 2 driver: protocol logic split into its own module
`era_arm/driver/protocol.py` (encode_command/parse_status) is separate from
`serial_arm.py` (the actual pyserial I/O) specifically so the wire-format logic
can be unit-tested (tests/test_protocol.py) without needing a real serial port
or connected hardware — mirrors the firmware's own split between
serial_protocol.cpp and main.cpp.
