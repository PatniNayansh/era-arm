"""Tests for Layer 4 — scripted teleop and the recording loop, against mocks."""

import numpy as np

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import MOTOR_KEYS, EraArmRobot, MockCamera, action_from_targets
from era_arm.teleop import ScriptedTeleop, record_episode, save_episode


def test_scripted_teleop_returns_flat_action_dicts():
    teleop = ScriptedTeleop([[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2]])
    teleop.start()
    assert teleop.get_action() == action_from_targets([1, 1, 1, 1, 1, 1])
    assert teleop.get_action() == action_from_targets([2, 2, 2, 2, 2, 2])
    assert teleop.get_action() == action_from_targets([2, 2, 2, 2, 2, 2])  # holds last


def test_scripted_teleop_loops():
    teleop = ScriptedTeleop([[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2]], loop=True)
    teleop.start()
    seen = [teleop.get_action() for _ in range(4)]
    assert seen[2] == action_from_targets([1, 1, 1, 1, 1, 1])  # wrapped around


def test_record_episode_length_and_alignment():
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=16, height=12)})
    robot.connect()
    poses = [[0, 0, 0, 0, 90, 0], [10, 20, 0, 0, 90, 45]]
    teleop = ScriptedTeleop(poses, loop=True)

    ep = record_episode(robot, teleop, fps=1000, max_steps=5, real_time=False)

    assert len(ep) == 5
    assert len(ep.observations) == 5
    assert ep.actions[0] == action_from_targets([0, 0, 0, 0, 90, 0])
    assert ep.actions[1] == action_from_targets([10, 20, 0, 0, 90, 45])
    assert "top" in ep.observations[0]
    assert "base.pos" in ep.observations[0]


def test_save_episode_uses_lerobot_feature_names(tmp_path):
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=8, height=8)})
    robot.connect()
    teleop = ScriptedTeleop([[0, 0, 0, 0, 90, 0]], loop=True)
    ep = record_episode(robot, teleop, max_steps=3, real_time=False)

    npz_path = save_episode(ep, tmp_path / "episode_000")

    assert npz_path.exists()
    assert (tmp_path / "episode_000.json").exists()
    data = np.load(npz_path)
    assert data["action"].shape == (3, len(MOTOR_KEYS))
    assert data["observation.state"].shape == (3, len(MOTOR_KEYS))
    assert data["observation.images.top"].shape == (3, 8, 8, 3)
