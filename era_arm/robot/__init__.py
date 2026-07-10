"""Layer 3 — robot: the arm plus its cameras as one observation/action interface."""

from era_arm.robot.camera import MockCamera, OpenCVCamera
from era_arm.robot.robot import EraArmRobot

__all__ = ["EraArmRobot", "MockCamera", "OpenCVCamera"]
