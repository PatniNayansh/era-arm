"""Layer 4 — ScriptedTeleop: replays a fixed list of poses.

Deterministic and hardware-free, so it drives the recording loop in tests and
demos. Poses are given as 6-angle lists; get_action() returns them as flat LeRobot
action dicts. Once past the last pose it holds the final pose (or loops, if asked).
"""

from __future__ import annotations

from era_arm.robot import action_from_targets
from era_arm.teleop.base import Teleoperator


class ScriptedTeleop(Teleoperator):
    def __init__(self, poses, loop: bool = False):
        if not poses:
            raise ValueError("poses must be a non-empty sequence of 6-angle lists")
        self._poses = [list(p) for p in poses]
        self._loop = loop
        self._i = 0

    def start(self) -> None:
        self._i = 0

    def get_action(self) -> dict:
        if self._i >= len(self._poses):
            if self._loop:
                self._i = 0
            else:
                return action_from_targets(self._poses[-1])  # hold the last pose
        pose = self._poses[self._i]
        self._i += 1
        return action_from_targets(pose)
