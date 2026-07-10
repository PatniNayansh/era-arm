# Layer 6 — Eval (`era_arm/eval`)

Runs a policy on the robot and records the trajectory. Observations and actions are
flat LeRobot dicts, matching Layer 3.

## Files

- `policy.py` — `Policy` interface (`select_action(obs_dict) -> action_dict`),
  `MockPolicy` (testing), `LeRobotPolicy` + `load_lerobot_policy(checkpoint)` which
  loads a trained checkpoint via LeRobot's real loader
  (`get_policy_class(cfg.type).from_pretrained(...)`).
- `rollout.py` — `rollout(robot, policy, steps, fps)` closed loop; returns a
  `Rollout` trajectory. Ideal for `MockPolicy` and programmatic control.
- `evaluate.py` — `build_eval_command(...)` + CLI: builds the `lerobot-record
  --policy.path=...` command that runs a trained policy on the real arm.

## Running a trained policy on the arm

The supported, maintained path is LeRobot's own control loop (it applies the
policy's preprocessor → policy → postprocessor pipeline against `LeRobotEraArm`):

```bash
# show the command (works anywhere):
uv run python -m era_arm.eval.evaluate \
    --checkpoint outputs/act-pick/checkpoints/last \
    --port /dev/era-arm --dataset you/era-arm-eval --episodes 10 --dry-run

# run it (needs `uv sync --extra train` + the arm):
uv run python -m era_arm.eval.evaluate --checkpoint ... --port /dev/era-arm --dataset ...
```

`LeRobotPolicy` is a convenience adapter for programmatic inference; validate it
against your installed LeRobot version before trusting it on hardware — the CLI
path above is the one to rely on.

## Testing the loop (no hardware / no model)

```python
from era_arm.eval import MockPolicy, rollout
traj = rollout(robot, MockPolicy(pose=[0,0,0,0,90,0]), steps=100)
```

Demo: `uv run python -m era_arm.eval.demo_rollout`
