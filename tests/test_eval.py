"""Tests for Layer 6 — policies and the rollout loop, against mocks."""

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.eval import MockPolicy, rollout
from era_arm.robot import EraArmRobot, MockCamera


def make_robot():
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=16, height=12)})
    robot.connect()
    return robot


def test_mock_policy_fixed_pose():
    policy = MockPolicy(pose=[1, 2, 3, 4, 90, 45])
    obs = {"joints": [0, 0, 0, 0, 0, 0]}
    assert policy.select_action(obs).tolist() == [1, 2, 3, 4, 90, 45]


def test_mock_policy_follow_joints_echoes_observation():
    policy = MockPolicy(follow_joints=True)
    obs = {"joints": [5, 5, 5, 5, 5, 5]}
    assert policy.select_action(obs).tolist() == [5, 5, 5, 5, 5, 5]


def test_rollout_runs_and_commands_arm():
    robot = make_robot()
    policy = MockPolicy(pose=[10, 20, 0, 0, 90, 45])
    traj = rollout(robot, policy, steps=6, fps=1000, real_time=False)

    assert len(traj) == 6
    assert len(traj.observations) == 6
    # The arm should have moved to the commanded pose.
    assert traj.observations[-1]["joints"].tolist() == [10.0, 20.0, 0.0, 0.0, 90.0, 45.0]


def test_rollout_out_of_range_action_raises():
    robot = make_robot()
    # 200 exceeds the shoulder limit; send_action -> driver -> format_command raises.
    import pytest

    with pytest.raises(ValueError):
        rollout(robot, MockPolicy(pose=[0, 200, 0, 0, 90, 0]), steps=1, real_time=False)
