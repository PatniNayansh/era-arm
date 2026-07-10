"""Tests for Layer 6 — policies, rollout loop, and the eval command builder."""

import pytest

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.eval import MockPolicy, build_eval_command, rollout
from era_arm.robot import MOTOR_KEYS, EraArmRobot, MockCamera, action_from_targets


def make_robot():
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=16, height=12)})
    robot.connect()
    return robot


def test_mock_policy_fixed_pose_returns_action_dict():
    policy = MockPolicy(pose=[1, 2, 3, 4, 90, 45])
    obs = {k: 0.0 for k in MOTOR_KEYS}
    assert policy.select_action(obs) == action_from_targets([1, 2, 3, 4, 90, 45])


def test_mock_policy_follow_joints_echoes_observation():
    policy = MockPolicy(follow_joints=True)
    obs = {k: 5.0 for k in MOTOR_KEYS}
    assert policy.select_action(obs) == action_from_targets([5, 5, 5, 5, 5, 5])


def test_rollout_runs_and_commands_arm():
    robot = make_robot()
    policy = MockPolicy(pose=[10, 20, 0, 0, 90, 45])
    traj = rollout(robot, policy, steps=6, fps=1000, real_time=False)

    assert len(traj) == 6
    assert len(traj.observations) == 6
    # The arm should have moved to the commanded pose.
    last = traj.observations[-1]
    assert [last[k] for k in MOTOR_KEYS] == [10.0, 20.0, 0.0, 0.0, 90.0, 45.0]


def test_rollout_out_of_range_action_raises():
    robot = make_robot()
    with pytest.raises(ValueError):
        rollout(robot, MockPolicy(pose=[0, 200, 0, 0, 90, 0]), steps=1, real_time=False)


def test_build_eval_command():
    cmd = build_eval_command(
        checkpoint="outputs/act/last", robot_port="/dev/era-arm",
        dataset_repo_id="you/era-arm-eval", num_episodes=5,
    )
    assert cmd[0] == "lerobot-record"
    assert "--robot.type=era_arm" in cmd
    assert "--robot.port=/dev/era-arm" in cmd
    assert "--policy.path=outputs/act/last" in cmd
    assert "--dataset.repo_id=you/era-arm-eval" in cmd
    assert "--dataset.num_episodes=5" in cmd
