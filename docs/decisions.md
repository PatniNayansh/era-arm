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

## Layer 2 driver: split protocol (pure) from transport (ArmDriver)
`era_arm/driver/protocol.py` holds the wire rules as pure functions
(`format_command`/`parse_status`) with no I/O, so they're unit-testable without
hardware; `arm.py`'s `ArmDriver` does the actual serial I/O and takes its
connection as a constructor argument (dependency injection). That lets the same
driver run against a real `serial.Serial` or the `FakeArm` mock unchanged — the
whole layer is built and tested (21 pytest tests) before any hardware exists.

## read_state() drains to the freshest line, not one-per-command
The firmware streams a status line every ~50 Hz tick regardless of commands, so
a naive one-readline-per-read returns stale buffered data. `read_state()` drains
everything currently buffered (`in_waiting`) and returns the last valid line,
skipping partial/garbled ones. Revisit if we later want the full history rather
than just latest.

## Software joint limits live in the driver (JOINT_LIMITS_DEG), currently placeholders
`format_command` validates targets against per-joint limits and raises (or clamps,
if `ArmDriver(clamp=True)`) before anything reaches a motor. Values in
`protocol.py` are placeholders — calibrate on the real arm and update here.

## Mock-first: every software layer is built and tested against fakes before hardware
No arm, cameras, or GPU exist in the current WSL setup, so each layer ships a
mock (`FakeArm`, `MockCamera`, `ScriptedTeleop`, `MockPolicy`) and a pytest suite
that runs with zero hardware. Real I/O is dependency-injected and swapped in later
(`ArmDriver.open`, `OpenCVCamera`, `KeyboardTeleop`, `load_lerobot_policy`). This
keeps the whole stack developable now and CI-testable on GitHub Actions.

## Heavy/hardware deps are optional extras, not core dependencies
Core install is just numpy + pyserial (fast, mock-testable). OpenCV, pynput, and
LeRobot/torch are `[project.optional-dependencies]` (`camera`, `teleop`, `train`),
installed per machine with `uv sync --extra <name>`. Their imports are lazy/guarded
so the package imports and tests pass without them.

## Training is a subprocess wrapper around lerobot-train, not a Python-API coupling
`era_arm/train/train.py` builds the exact `lerobot-train` command and shells out,
rather than importing lerobot's fast-moving training API. `build_train_command()`
stays pure and unit-tested; only actually running it needs the `train` extra + CUDA.

## Recorded episodes use a lightweight .npz format, converted to LeRobotDataset later
`save_episode` writes numpy `.npz` + JSON so recording works with no heavy deps.
Arrays use LeRobot's dataset feature names (`observation.state`,
`observation.images.<cam>`, `action`) so they line up with the real pipeline. For
real training data, `lerobot-record` builds the video-encoded LeRobotDataset
directly; the `.npz` recorder is for offline/CI use. Revisit for large/streaming data.

## Conform to LeRobot's Robot interface (verified from source), not invented naming
Initial L3-L6 used ad-hoc keys (`joints` array, `image.top`) and a guessed policy
loader — a code review flagged they wouldn't match LeRobot. Re-verified the real API
from LeRobot source + the "Bring Your Own Hardware" guide and adopted it: flat dicts
keyed `"<joint>.pos"` for state/action, camera-name keys for frames, lifecycle
`connect(calibrate=True)/disconnect/configure/calibrate`, `observation_features`/
`action_features`. This makes the arm a drop-in for LeRobot's data/train/eval tools.

## Two robot classes: light duck-typed core + registered LeRobot subclass
`EraArmRobot` (robot.py) matches LeRobot's interface but imports no lerobot, so it
stays mock-testable in CI. `LeRobotEraArm` (lerobot_robot.py) is the real
`lerobot.robots.Robot` subclass, registered via `RobotConfig.register_subclass("era_arm")`
so `lerobot-record`/`lerobot-teleoperate`/`lerobot-eval` discover it. Both share one
mapping in robot.py — single source of truth, guarded lerobot import.

## Delegate real training/inference to LeRobot CLIs; don't hand-roll the pipeline
Loading uses LeRobot's real `from_pretrained` (via `get_policy_class(cfg.type)`), and
closed-loop inference on hardware goes through `lerobot-record --policy.path` /
`lerobot-eval`, which run the maintained preprocessor→policy→postprocessor pipeline.
`build_train_command`/`build_eval_command` are pure, unit-tested wrappers. Our
`rollout`/`MockPolicy` remain for testing the loop mechanics without a model.
