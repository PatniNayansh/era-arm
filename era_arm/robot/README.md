# Layer 3 — Robot (`era_arm/robot`)

Bundles the Layer 2 `ArmDriver` with cameras into a **LeRobot-shaped robot**:
observations and actions are flat dicts keyed the LeRobot way, so our arm plugs
straight into LeRobot's data-collection, training, and inference tooling.

## The interface (matches `lerobot.robots.Robot`)

```python
observation = {
  "base.pos": 10.0, "shoulder.pos": 20.0, ..., "gripper.pos": 45.0,  # <joint>.pos
  "top": np.uint8[H, W, 3],                                          # one per camera
}
action = {"base.pos": 10.0, ..., "gripper.pos": 45.0}                # <joint>.pos
```

Lifecycle mirrors LeRobot exactly: `connect(calibrate=True)`, `disconnect()`,
`configure()`, `calibrate()`, and the `is_connected` / `is_calibrated` /
`observation_features` / `action_features` properties. The safety watchdog isn't a
policy feature, so it's exposed via `robot.read_watchdog()` rather than in the obs.

## Two robots, one driver

- **`robot.py` → `EraArmRobot`** — light, **duck-typed**, mock-testable. Does *not*
  import lerobot, so it runs in CI and offline dev. Use it with our own record /
  rollout loops and with any LeRobot function that accepts a Robot-like object.
- **`lerobot_robot.py` → `LeRobotEraArm` + `EraArmRobotConfig`** — the real
  `lerobot.robots.Robot` subclass, registered as `era_arm`, so the LeRobot CLIs
  discover it. Importing it requires lerobot (`uv sync --extra train`).

Both share one mapping (`action_from_targets` / `targets_from_action` /
`state_from_angles` in `robot.py`), so there's a single source of truth.

## Cameras (`camera.py`)

`MockCamera` (deterministic synthetic frames, no hardware) and `OpenCVCamera` (real
USB webcam via lazy `import cv2`; native Ubuntu only). Both expose `read()` and the
`async_read()` alias LeRobot's loop calls.

## Usage

```python
from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import EraArmRobot, MockCamera, action_from_targets

robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera()})
with robot:
    obs = robot.get_observation()
    robot.send_action(action_from_targets([0, 0, 0, 0, 90, 0]))
```

Real hardware, driven by the LeRobot CLI (after `uv sync --extra train`):

```bash
lerobot-teleoperate --robot.type=era_arm --robot.port=/dev/era-arm ...
lerobot-record      --robot.type=era_arm --robot.port=/dev/era-arm \
                    --dataset.repo_id=you/era-arm-pick --dataset.num_episodes=30 ...
```
