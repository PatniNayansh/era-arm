# Layer 3 — Robot (`era_arm/robot`)

Bundles the Layer 2 `ArmDriver` with cameras into one `EraArmRobot` object exposing
a LeRobot-style interface. This is what the recording (L4) and evaluation (L6)
layers drive.

## Files

- `camera.py` — `MockCamera` (deterministic synthetic frames, no hardware) and
  `OpenCVCamera` (real USB webcam via a lazy `import cv2`; native-Ubuntu only).
- `robot.py` — `EraArmRobot(driver, cameras=None)`: `connect()`, `disconnect()`,
  `get_observation()`, `send_action()`, plus `action_features` /
  `observation_features` and context-manager support.

## Observation / action shape

```python
obs = {
  "joints":  np.float32[6],   # measured joint angles, degrees
  "watchdog": bool,           # arm stopped itself for safety?
  "image.<name>": np.uint8[H, W, 3],  # one RGB frame per camera
}
action = np.float32[6]        # six target joint angles, degrees
```

## Usage

```python
from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import EraArmRobot, MockCamera

robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera()})
with robot:                         # connect() / disconnect() automatically
    obs = robot.get_observation()
    robot.send_action([0, 0, 0, 0, 90, 0])
```

Real hardware later: swap `FakeArm()` for `ArmDriver.open("/dev/ttyUSB0")` and
`MockCamera()` for `OpenCVCamera(index=0)` (needs the `camera` extra:
`uv sync --extra camera`).
