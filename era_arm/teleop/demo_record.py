"""End-to-end recording demo — no hardware. Records a short episode from a
scripted teleoperator driving the mock arm, then reports what it captured.

Run it with:   uv run python -m era_arm.teleop.demo_record
"""

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm
from era_arm.robot import EraArmRobot, MockCamera
from era_arm.teleop.record import record_episode
from era_arm.teleop.scripted import ScriptedTeleop

POSES = [
    [0, 0, 0, 0, 90, 0],
    [10, 20, 0, 0, 90, 45],
    [-20, -10, 30, 10, 45, 90],
    [0, 0, 0, 0, 90, 0],
]


def main():
    robot = EraArmRobot(ArmDriver(FakeArm()), cameras={"top": MockCamera(width=64, height=48)})
    robot.connect()
    teleop = ScriptedTeleop(POSES, loop=True)

    episode = record_episode(robot, teleop, fps=30, max_steps=10, real_time=False)

    print(f"recorded {len(episode)} steps at {episode.fps} fps")
    print("first action: ", episode.actions[0])
    print("last action:  ", episode.actions[-1])
    print("obs keys:     ", sorted(episode.observations[0]))
    robot.disconnect()


if __name__ == "__main__":
    main()
