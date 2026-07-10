"""Tests for Layer 3 — EraArmRobot and cameras, against mocks."""

import numpy as np
import pytest

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import EraArmRobot, MockCamera


def make_robot(with_camera=True):
    cameras = {"top": MockCamera(width=32, height=24)} if with_camera else None
    return EraArmRobot(ArmDriver(FakeArm()), cameras=cameras)


def test_mock_camera_shape_and_advances():
    cam = MockCamera(width=16, height=8)
    a = cam.read()
    b = cam.read()
    assert a.shape == (8, 16, 3)
    assert a.dtype == np.uint8
    assert not np.array_equal(a, b)  # successive frames differ


def test_get_observation_has_joints_and_image():
    robot = make_robot()
    robot.connect()
    obs = robot.get_observation()
    assert obs["joints"].shape == (6,)
    assert obs["joints"].dtype == np.float32
    assert obs["image.top"].shape == (24, 32, 3)
    assert obs["watchdog"] is False


def test_send_action_roundtrips_through_driver():
    robot = make_robot(with_camera=False)
    robot.connect()
    robot.send_action([10, 20, 0, 0, 90, 45])
    assert robot.get_observation()["joints"].tolist() == [10.0, 20.0, 0.0, 0.0, 90.0, 45.0]


def test_send_action_wrong_length_raises():
    robot = make_robot(with_camera=False)
    with pytest.raises(ValueError):
        robot.send_action([1, 2, 3])


def test_context_manager_connects_and_disconnects():
    robot = make_robot()
    with robot as r:
        assert r.is_connected is True
    assert robot.is_connected is False


def test_feature_specs():
    robot = make_robot()
    assert robot.action_features["shape"] == (6,)
    assert robot.observation_features["image.top"]["shape"] == (24, 32, 3)
