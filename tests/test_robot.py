"""Tests for Layer 3 — EraArmRobot (LeRobot-shaped) and cameras, against mocks."""

import numpy as np
import pytest

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import (
    MOTOR_KEYS,
    EraArmRobot,
    MockCamera,
    action_from_targets,
    targets_from_action,
)


def make_robot(with_camera=True):
    cameras = {"top": MockCamera(width=32, height=24)} if with_camera else None
    return EraArmRobot(ArmDriver(FakeArm()), cameras=cameras)


def test_motor_keys_are_lerobot_style():
    assert MOTOR_KEYS == (
        "base.pos", "shoulder.pos", "elbow.pos", "wrist_pitch.pos",
        "wrist_roll.pos", "gripper.pos",
    )


def test_action_target_roundtrip_helpers():
    action = action_from_targets([10, 20, 0, 0, 90, 45])
    assert action == {
        "base.pos": 10.0, "shoulder.pos": 20.0, "elbow.pos": 0.0,
        "wrist_pitch.pos": 0.0, "wrist_roll.pos": 90.0, "gripper.pos": 45.0,
    }
    assert targets_from_action(action) == [10.0, 20.0, 0.0, 0.0, 90.0, 45.0]


def test_mock_camera_shape_and_advances():
    cam = MockCamera(width=16, height=8)
    a, b = cam.read(), cam.async_read()
    assert a.shape == (8, 16, 3) and a.dtype == np.uint8
    assert not np.array_equal(a, b)


def test_observation_is_flat_lerobot_dict():
    robot = make_robot()
    robot.connect()
    obs = robot.get_observation()
    # motor positions keyed "<joint>.pos", camera keyed by its name, no extras.
    assert set(obs) == set(MOTOR_KEYS) | {"top"}
    assert obs["base.pos"] == 0.0
    assert obs["top"].shape == (24, 32, 3)
    assert robot.read_watchdog() is False


def test_observation_and_action_features():
    robot = make_robot()
    assert robot.action_features == {k: float for k in MOTOR_KEYS}
    assert robot.observation_features["top"] == (24, 32, 3)


def test_send_action_roundtrips_through_driver():
    robot = make_robot(with_camera=False)
    robot.connect()
    robot.send_action(action_from_targets([10, 20, 0, 0, 90, 45]))
    obs = robot.get_observation()
    assert [obs[k] for k in MOTOR_KEYS] == [10.0, 20.0, 0.0, 0.0, 90.0, 45.0]


def test_send_action_missing_joint_raises():
    robot = make_robot(with_camera=False)
    robot.connect()
    with pytest.raises(ValueError):
        robot.send_action({"base.pos": 0.0})  # missing the other five


def test_io_before_connect_raises():
    robot = make_robot(with_camera=False)
    with pytest.raises(ConnectionError):
        robot.get_observation()


def test_context_manager_connects_and_disconnects():
    robot = make_robot()
    with robot as r:
        assert r.is_connected is True
    assert robot.is_connected is False
