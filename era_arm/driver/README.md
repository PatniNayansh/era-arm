# Layer 2 — Python Driver (`era_arm/driver`)

The Python side of the USB-serial link to the ESP32 firmware (Layer 1). Turns
high-level "move to these joint angles" calls into the wire protocol and back,
so the layers above (robot, teleop, ...) never touch a serial port.

## Files

- `protocol.py` — the pure text/number rules, no hardware. `format_command()`
  (angles → command bytes), `parse_status()` (status bytes → `ArmState`), plus
  joint-limit validation (`validate_targets`, `clamp_targets`) and the
  `JOINT_LIMITS_DEG` / `JOINT_NAMES` constants.
- `arm.py` — `ArmDriver`, the object everything upstream uses: `send_targets()`,
  `read_state()`, `close()`, context-manager support, and `ArmDriver.open(port)`
  for real hardware.
- `mock.py` — `FakeArm`, a pure-Python stand-in for the ESP32 that mimics
  pyserial (`write`/`readline`/`in_waiting`) and streams status like the real
  firmware. Lets us build and test without hardware.
- `demo.py` — runnable end-to-end demo against the mock.

## Protocol

```
Host -> MCU:  P,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>\n        target angles, degrees
MCU  -> Host: S,<j0>,...,<j5>,<millis>,<watchdog>\n    status, degrees
```
`watchdog` = 1 means the arm stopped itself (no command in the last 500 ms).
Baud 115200, ASCII.

## Usage

```python
from era_arm.driver.arm import ArmDriver

# Real hardware (once wired):
with ArmDriver.open("/dev/ttyUSB0") as arm:
    arm.send_targets([0, 0, 0, 0, 90, 0])
    print(arm.read_state().angles)

# No hardware — test against the mock:
from era_arm.driver.mock import FakeArm
arm = ArmDriver(FakeArm())
```

Pass `clamp=True` to `ArmDriver(...)` / `.open(...)` to pull out-of-range targets
to the nearest safe angle instead of raising `ValueError`.

## Run it

```
uv run python -m era_arm.driver.demo   # end-to-end demo (mock)
uv run pytest                          # the test suite (21 tests)
```

## Status / known gaps

- Built and tested against `FakeArm`; **not yet run on real hardware.**
- `JOINT_LIMITS_DEG` in `protocol.py` are **placeholders** — measure and
  calibrate on the real arm, then record in `docs/decisions.md`.
- `read_state()` drains the buffered stream and returns the freshest valid line.
  No PID/closed-loop control here — the driver only commands and reports.
