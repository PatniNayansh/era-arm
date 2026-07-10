"""Layer 3 — robot: the arm plus its cameras as a LeRobot-shaped robot.

`lerobot_robot` is intentionally NOT imported here — it subclasses lerobot's Robot
and needs the `train` extra. Import it explicitly only where lerobot is installed:
`from era_arm.robot.lerobot_robot import LeRobotEraArm, EraArmRobotConfig`.
"""

from era_arm.robot.camera import MockCamera, OpenCVCamera
from era_arm.robot.robot import (
    MOTOR_KEYS,
    EraArmRobot,
    action_from_targets,
    state_from_angles,
    targets_from_action,
)

__all__ = [
    "EraArmRobot",
    "MockCamera",
    "OpenCVCamera",
    "MOTOR_KEYS",
    "action_from_targets",
    "targets_from_action",
    "state_from_angles",
]
