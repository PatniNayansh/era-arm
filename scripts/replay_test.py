"""Replay a recorded episode's actions on an arm — a data-sanity check.

Reads the actions from an episode saved by era_arm.teleop.record.save_episode
(a .npz) and streams them to an ArmDriver at the episode's fps. By default it
runs against the FakeArm mock (so it works with no hardware); pass --port to
replay on the real arm.

    uv run python scripts/replay_test.py datasets/episode_000.npz
    uv run python scripts/replay_test.py datasets/episode_000.npz --port /dev/era-arm

`replay_actions()` is a pure loop over a driver, so it's unit-tested against the mock.
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm


def load_actions(npz_path) -> np.ndarray:
    """Return the (T, 6) action array from a saved episode .npz.

    Episodes saved by era_arm.teleop.record use LeRobot's feature name `action`.
    """
    with np.load(npz_path) as data:
        return np.asarray(data["action"], dtype=np.float32)


def replay_actions(driver: ArmDriver, actions, fps: int = 30, real_time: bool = True) -> int:
    """Send each action to `driver` at `fps`. Returns the number of steps sent."""
    period = 1.0 / fps
    count = 0
    for action in actions:
        t0 = time.perf_counter()
        driver.send_targets(np.asarray(action, dtype=np.float32).tolist())
        driver.read_state()  # keep the status stream drained
        count += 1
        if real_time:
            remaining = period - (time.perf_counter() - t0)
            if remaining > 0:
                time.sleep(remaining)
    return count


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Replay an episode's actions on the arm.")
    parser.add_argument("episode", help="path to an episode .npz")
    parser.add_argument("--port", default=None, help="serial port (omit to use the mock arm)")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args(argv)

    actions = load_actions(args.episode)
    driver = ArmDriver.open(args.port) if args.port else ArmDriver(FakeArm())
    try:
        n = replay_actions(driver, actions, fps=args.fps)
    finally:
        driver.close()
    print(f"replayed {n} steps from {args.episode}"
          f" on {'the real arm' if args.port else 'the mock arm'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
