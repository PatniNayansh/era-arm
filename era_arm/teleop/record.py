"""Layer 4 — recording demonstrations.

Runs the robot and a teleoperator together at a fixed rate, pairing each
observation with the action taken, into an Episode. Observations and actions are
flat LeRobot dicts ("<joint>.pos" + camera-name keys). `save_episode` writes a
compressed .npz whose arrays already use LeRobot's dataset feature names
(`observation.state`, `observation.images.<cam>`, `action`) plus a JSON sidecar.

SEAM: the fully-supported way to record real training data is LeRobot's own
`lerobot-record` CLI driving `LeRobotEraArm` (era_arm/robot/lerobot_robot.py); it
builds a proper video-encoded LeRobotDataset. This lightweight recorder exists so
the loop is testable with zero heavy dependencies — see era_arm/train/README.md.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from era_arm.robot import MOTOR_KEYS


@dataclass
class Episode:
    """One recorded demonstration: aligned observations and actions (flat dicts)."""

    observations: list = field(default_factory=list)  # list[dict] from robot.get_observation()
    actions: list = field(default_factory=list)        # list[dict] flat "<joint>.pos" actions
    fps: int = 30

    def __len__(self) -> int:
        return len(self.actions)


def record_episode(robot, teleop, fps: int = 30, max_steps: int | None = None,
                   real_time: bool = True) -> Episode:
    """Drive `robot` with `teleop` at `fps`, recording each step.

    Records observation-then-action each tick (the imitation-learning convention:
    observation[t] is the state the action[t] responded to). Runs until `max_steps`
    (or, if None, until KeyboardInterrupt). Set `real_time=False` to skip the
    per-tick sleep (used by tests so they run instantly).
    """
    episode = Episode(fps=fps)
    period = 1.0 / fps
    teleop.start()
    step = 0
    try:
        while max_steps is None or step < max_steps:
            t0 = time.perf_counter()
            obs = robot.get_observation()
            action = teleop.get_action()
            robot.send_action(action)
            episode.observations.append(obs)
            episode.actions.append(dict(action))
            step += 1
            if real_time:
                remaining = period - (time.perf_counter() - t0)
                if remaining > 0:
                    time.sleep(remaining)
    except KeyboardInterrupt:
        pass
    finally:
        teleop.stop()
    return episode


def save_episode(episode: Episode, path) -> Path:
    """Save an Episode to `<path>.npz` (+ `<path>.json`). Returns the .npz path.

    Arrays use LeRobot dataset feature names so conversion later is a rename-free
    map: `action` (T,6), `observation.state` (T,6), and one
    `observation.images.<cam>` (T,H,W,3) per camera. `watchdog` (T,) is kept too.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def stack_motor(dicts):
        return np.array([[float(d[k]) for k in MOTOR_KEYS] for d in dicts], dtype=np.float32)

    arrays: dict = {
        "action": stack_motor(episode.actions) if episode.actions
        else np.zeros((0, len(MOTOR_KEYS)), np.float32),
    }
    if episode.observations:
        arrays["observation.state"] = stack_motor(episode.observations)
        cam_keys = [k for k in episode.observations[0] if k not in MOTOR_KEYS]
        for cam in cam_keys:
            arrays[f"observation.images.{cam}"] = np.stack(
                [o[cam] for o in episode.observations]
            )

    npz_path = path.with_suffix(".npz")
    np.savez_compressed(npz_path, **arrays)

    meta = {"length": len(episode), "fps": episode.fps, "features": sorted(arrays)}
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    return npz_path
