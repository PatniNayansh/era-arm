# Layer 4 — Teleop (`era_arm/teleop`)

Human (or scripted) control of the arm, and recording demonstrations. Actions are
flat LeRobot dicts (`{"base.pos": 10.0, ...}`), matching `robot.send_action`.

## Files

- `base.py` — `Teleoperator` interface: `start()`, `get_action() -> dict`, `stop()`.
- `scripted.py` — `ScriptedTeleop(poses)`: replays a fixed pose list as action dicts.
  Deterministic; used in demos/tests.
- `keyboard.py` — `KeyboardTeleop`: nudge each joint from the keyboard (needs a
  terminal + the `teleop` extra: `uv sync --extra teleop`). Real-use only.
- `record.py` — `record_episode(robot, teleop, fps, max_steps)` runs the loop and
  pairs observations↔actions into an `Episode`; `save_episode()` writes a `.npz`
  whose arrays already use LeRobot feature names (`observation.state`,
  `observation.images.<cam>`, `action`) plus a `.json` sidecar.

## Two recording paths

- **Real training data → use LeRobot's `lerobot-record`** driving `LeRobotEraArm`
  (Layer 3). It builds a proper video-encoded `LeRobotDataset` and handles cameras,
  timestamps, and episode management:

  ```bash
  lerobot-record --robot.type=era_arm --robot.port=/dev/era-arm \
      --teleop.type=<your-teleop> \
      --dataset.repo_id=you/era-arm-pick --dataset.num_episodes=30
  ```

- **Offline / CI → our lightweight recorder** (no heavy deps), for testing the loop
  and quick captures against the mock:

  ```python
  from era_arm.teleop import ScriptedTeleop, record_episode, save_episode
  ep = record_episode(robot, ScriptedTeleop(poses, loop=True), fps=30, max_steps=100)
  save_episode(ep, "datasets/episode_000")
  ```

Demo (no hardware): `uv run python -m era_arm.teleop.demo_record`
