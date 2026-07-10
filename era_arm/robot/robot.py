"""Layer 3 — EraArmRobot: the arm + its cameras as one 'robot' object.

This is the interface the data-collection (L4) and evaluation (L6) layers talk to.
It bundles the Layer 2 ArmDriver together with zero or more cameras and exposes a
LeRobot-style surface: connect / get_observation / send_action / disconnect. The
observation and action shapes here are what the recorded dataset and the trained
policy will use, so they're deliberately simple and explicit.
"""

from __future__ import annotations

import numpy as np

from era_arm.driver.arm import ArmDriver
from era_arm.driver.protocol import JOINT_NAMES, NUM_JOINTS


class EraArmRobot:
    """A 6-joint arm plus named cameras.

    `driver` is a Layer 2 ArmDriver (real or backed by FakeArm). `cameras` maps a
    name -> camera object (MockCamera / OpenCVCamera); pass None for no cameras.
    """

    def __init__(self, driver: ArmDriver, cameras: dict | None = None):
        self.driver = driver
        self.cameras = dict(cameras) if cameras else {}
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        for cam in self.cameras.values():
            cam.connect()
        self._connected = True

    def disconnect(self) -> None:
        for cam in self.cameras.values():
            cam.disconnect()
        self.driver.close()
        self._connected = False

    def get_observation(self) -> dict:
        """Read the arm's current state and every camera into one observation dict.

        Returns:
            {
              "joints":  float32 array of 6 measured joint angles (degrees),
              "watchdog": bool (True == arm stopped itself for safety),
              "image.<name>": uint8 HxWx3 RGB frame, one per camera,
            }
        """
        state = self.driver.read_state()
        obs: dict = {
            "joints": np.asarray(state.angles, dtype=np.float32),
            "watchdog": state.watchdog,
        }
        for name, cam in self.cameras.items():
            obs[f"image.{name}"] = cam.read()
        return obs

    def send_action(self, action) -> np.ndarray:
        """Command six target joint angles. Returns the action actually sent."""
        action = np.asarray(action, dtype=np.float32)
        if action.shape != (NUM_JOINTS,):
            raise ValueError(f"action must be {NUM_JOINTS} angles, got shape {action.shape}")
        self.driver.send_targets(action.tolist())
        return action

    @property
    def action_features(self) -> dict:
        """Names/shape of an action — used when building the dataset/policy."""
        return {"names": list(JOINT_NAMES), "shape": (NUM_JOINTS,)}

    @property
    def observation_features(self) -> dict:
        feats = {"joints": {"names": list(JOINT_NAMES), "shape": (NUM_JOINTS,)}}
        for name, cam in self.cameras.items():
            feats[f"image.{name}"] = {"shape": (cam.height, cam.width, 3)}
        return feats

    def __enter__(self) -> "EraArmRobot":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.disconnect()
