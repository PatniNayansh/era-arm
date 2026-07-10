"""Layer 4 — recording demonstrations.

Runs the robot and a teleoperator together at a fixed rate, pairing each
observation with the action taken, into an Episode. `save_episode` writes it to
disk as a compressed .npz plus a JSON sidecar.

SEAM: this is intentionally a lightweight, dependency-free format so we can record
and test today. When `lerobot` is installed, `save_episode` is where episodes get
converted into a `LeRobotDataset` (video-encoded observations + a HF dataset) for
training — see era_arm/train/README.md.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Episode:
    """One recorded demonstration: aligned observations and actions."""

    observations: list = field(default_factory=list)  # list[dict] from robot.get_observation()
    actions: list = field(default_factory=list)        # list[np.float32[6]]
    fps: int = 30

    def __len__(self) -> int:
        return len(self.actions)


def record_episode(robot, teleop, fps: int = 30, max_steps: int | None = None,
                   real_time: bool = True) -> Episode:
    """Drive `robot` with `teleop` at `fps`, recording each step.

    Records observation-then-action each tick. Runs until `max_steps` (or, if
    None, until KeyboardInterrupt). Set `real_time=False` to skip the per-tick
    sleep (used by tests so they run instantly).
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
            episode.actions.append(np.asarray(action, dtype=np.float32))
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
    """Save an Episode to `<path>.npz` (+ `<path>.json` metadata). Returns the .npz path.

    Arrays saved: `actions` (T,6), `joints` (T,6), `watchdog` (T,), and one
    `image.<name>` (T,H,W,3) array per camera present in the observations.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    arrays: dict = {
        "actions": np.stack(episode.actions) if episode.actions else np.zeros((0, 6), np.float32),
    }
    if episode.observations:
        arrays["joints"] = np.stack([o["joints"] for o in episode.observations])
        arrays["watchdog"] = np.array([o["watchdog"] for o in episode.observations], dtype=bool)
        image_keys = [k for k in episode.observations[0] if k.startswith("image.")]
        for key in image_keys:
            arrays[key] = np.stack([o[key] for o in episode.observations])

    npz_path = path.with_suffix(".npz")
    np.savez_compressed(npz_path, **arrays)

    meta = {"length": len(episode), "fps": episode.fps, "arrays": sorted(arrays)}
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    return npz_path
