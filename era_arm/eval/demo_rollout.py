"""End-to-end eval demo — no hardware, no model. Runs a MockPolicy on the mock
arm and reports the trajectory it produced.

Run it with:   uv run python -m era_arm.eval.demo_rollout
"""

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.eval.policy import MockPolicy
from era_arm.eval.rollout import rollout
from era_arm.robot import MOTOR_KEYS, EraArmRobot, MockCamera


def main():
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=64, height=48)})
    robot.connect()
    policy = MockPolicy(pose=[10, 20, 0, 0, 90, 45])

    traj = rollout(robot, policy, steps=8, fps=30, real_time=False)

    print(f"ran {len(traj)} steps at {traj.fps} fps")
    print("commanded action:", traj.actions[0])
    print("arm ended at:     ", {k: traj.observations[-1][k] for k in MOTOR_KEYS})
    robot.disconnect()


if __name__ == "__main__":
    main()
