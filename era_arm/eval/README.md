# Layer 6 — Eval (`era_arm/eval`)

Runs a policy on the robot in a closed loop and records the trajectory — the same
loop used for measuring success rate and for deployment.

## Files

- `policy.py` — `Policy` interface (`select_action(obs)`), `MockPolicy` (testing),
  and `load_lerobot_policy(checkpoint)` for a trained LeRobot policy (lazy import
  of lerobot/torch; needs the `train` extra + CUDA).
- `rollout.py` — `rollout(robot, policy, steps, fps)` closed loop; returns a
  `Rollout` trajectory.

## Usage

```python
from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import EraArmRobot
from era_arm.eval import MockPolicy, rollout

robot = EraArmRobot(ArmDriver(FakeArm()))
robot.connect()
traj = rollout(robot, MockPolicy(pose=[0,0,0,0,90,0]), steps=100)
```

With a trained model (GPU box, `uv sync --extra train`):

```python
from era_arm.eval import load_lerobot_policy, rollout
policy = load_lerobot_policy("outputs/act-pick/checkpoints/last")
traj = rollout(ArmDriver.open("/dev/ttyUSB0")-backed robot, policy, steps=300)
```

Demo (no hardware/model): `uv run python -m era_arm.eval.demo_rollout`
