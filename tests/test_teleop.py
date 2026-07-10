"""Tests for Layer 4 — scripted teleop and the recording loop, against mocks."""

import numpy as np

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import EraArmRobot, MockCamera
from era_arm.teleop import ScriptedTeleop, record_episode, save_episode


def test_scripted_teleop_sequence_then_holds():
    teleop = ScriptedTeleop([[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2]])
    teleop.start()
    assert teleop.get_action() == [1, 1, 1, 1, 1, 1]
    assert teleop.get_action() == [2, 2, 2, 2, 2, 2]
    assert teleop.get_action() == [2, 2, 2, 2, 2, 2]  # holds last


def test_scripted_teleop_loops():
    teleop = ScriptedTeleop([[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2]], loop=True)
    teleop.start()
    seen = [teleop.get_action() for _ in range(4)]
    assert seen[2] == [1, 1, 1, 1, 1, 1]  # wrapped around


def test_record_episode_length_and_alignment():
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=16, height=12)})
    robot.connect()
    poses = [[0, 0, 0, 0, 90, 0], [10, 20, 0, 0, 90, 45]]
    teleop = ScriptedTeleop(poses, loop=True)

    ep = record_episode(robot, teleop, fps=1000, max_steps=5, real_time=False)

    assert len(ep) == 5
    assert len(ep.observations) == 5
    assert ep.actions[0].tolist() == [0, 0, 0, 0, 90, 0]
    assert ep.actions[1].tolist() == [10, 20, 0, 0, 90, 45]
    assert "image.top" in ep.observations[0]


def test_save_episode_writes_npz_and_json(tmp_path):
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=8, height=8)})
    robot.connect()
    teleop = ScriptedTeleop([[0, 0, 0, 0, 90, 0]], loop=True)
    ep = record_episode(robot, teleop, max_steps=3, real_time=False)

    npz_path = save_episode(ep, tmp_path / "episode_000")

    assert npz_path.exists()
    assert (tmp_path / "episode_000.json").exists()
    data = np.load(npz_path)
    assert data["actions"].shape == (3, 6)
    assert data["joints"].shape == (3, 6)
    assert data["image.top"].shape == (3, 8, 8, 3)
