"""Tests for scripts — replay loop against the mock arm."""

import numpy as np

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm

# scripts/ isn't a package; load replay_test.py by path.
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "replay_test", Path(__file__).resolve().parents[1] / "scripts" / "replay_test.py"
)
replay_test = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(replay_test)


def test_replay_actions_sends_every_step():
    fake = FakeArm()
    driver = ArmDriver(fake)
    actions = np.array([[0, 0, 0, 0, 90, 0], [10, 20, 0, 0, 90, 45]], dtype=np.float32)

    n = replay_test.replay_actions(driver, actions, fps=1000, real_time=False)

    assert n == 2
    # After the last action the fake arm sits at that pose.
    assert fake.angles == [10.0, 20.0, 0.0, 0.0, 90.0, 45.0]


def test_load_actions_roundtrips(tmp_path):
    from era_arm.driver.mock import FakeArm  # noqa: F811
    from era_arm.robot import EraArmRobot
    from era_arm.teleop import ScriptedTeleop, record_episode, save_episode

    robot = EraArmRobot(ArmDriver(FakeArm()))
    robot.connect()
    ep = record_episode(robot, ScriptedTeleop([[0, 0, 0, 0, 90, 0]], loop=True),
                        max_steps=3, real_time=False)
    npz_path = save_episode(ep, tmp_path / "ep")

    actions = replay_test.load_actions(npz_path)
    assert actions.shape == (3, 6)
