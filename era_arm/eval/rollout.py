"""Layer 6 — running a policy on the robot (a 'rollout').

The closed loop that evaluation and deployment share: read an observation, ask the
policy for an action, send it to the arm, repeat at a fixed rate. Returns the
recorded trajectory so callers can score success or inspect behaviour.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Rollout:
    observations: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    fps: int = 30

    def __len__(self) -> int:
        return len(self.actions)


def rollout(robot, policy, steps: int, fps: int = 30, real_time: bool = True) -> Rollout:
    """Run `policy` on `robot` for `steps` ticks and return the trajectory.

    Set `real_time=False` to skip the per-tick sleep (tests run instantly).
    """
    traj = Rollout(fps=fps)
    period = 1.0 / fps
    if hasattr(policy, "reset"):
        policy.reset()
    try:
        for _ in range(steps):
            t0 = time.perf_counter()
            obs = robot.get_observation()
            action = policy.select_action(obs)
            robot.send_action(action)
            traj.observations.append(obs)
            traj.actions.append(np.asarray(action, dtype=np.float32))
            if real_time:
                remaining = period - (time.perf_counter() - t0)
                if remaining > 0:
                    time.sleep(remaining)
    except KeyboardInterrupt:
        pass
    return traj
