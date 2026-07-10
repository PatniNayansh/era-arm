# Layer 4 — Teleop (`era_arm/teleop`)

Human (or scripted) control of the arm, and recording those demonstrations into
episodes for training.

## Files

- `base.py` — `Teleoperator` interface: `start()`, `get_action()`, `stop()`.
- `scripted.py` — `ScriptedTeleop(poses)`: replays a fixed pose list. Deterministic,
  used in demos/tests.
- `keyboard.py` — `KeyboardTeleop`: nudge each joint with the keyboard (needs a
  terminal + the `teleop` extra: `uv sync --extra teleop`). Real-use only.
- `record.py` — `record_episode(robot, teleop, fps, max_steps)` runs the control
  loop and pairs observations↔actions into an `Episode`; `save_episode()` writes
  `.npz` + `.json`.

## Recording

```python
from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import EraArmRobot, MockCamera
from era_arm.teleop import ScriptedTeleop, record_episode, save_episode

robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera()})
robot.connect()
teleop = ScriptedTeleop([[0,0,0,0,90,0], [10,20,0,0,90,45]], loop=True)

episode = record_episode(robot, teleop, fps=30, max_steps=100)
save_episode(episode, "datasets/episode_000")
```

Demo (no hardware): `uv run python -m era_arm.teleop.demo_record`

## Note on the dataset format

`save_episode` uses a lightweight `.npz` format so recording works with zero heavy
dependencies. Converting episodes into a **LeRobotDataset** (the video-encoded
format the training scripts consume) is the seam documented in
`era_arm/train/README.md`, wired up once `lerobot` is installed.
