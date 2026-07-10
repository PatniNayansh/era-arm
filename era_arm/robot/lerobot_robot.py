"""Layer 3 — the real, CLI-discoverable LeRobot Robot for the era-arm.

This subclasses lerobot's `Robot` and registers a config, so the LeRobot command-line
tools (`lerobot-record`, `lerobot-teleoperate`, `lerobot-eval`) drive the physical arm
directly, using our Layer 2 ArmDriver for motor I/O. It is separate from
`era_arm.robot.robot.EraArmRobot` (the light, mock-testable, duck-typed version)
because importing it REQUIRES lerobot to be installed:

    uv sync --extra train      # installs lerobot

Then, e.g.:

    lerobot-record \
        --robot.type=era_arm --robot.port=/dev/era-arm \
        --dataset.repo_id=you/era-arm-pick --dataset.num_episodes=30 \
        --teleop.type=<your-teleop>

The mapping between our flat "<joint>.pos" dicts and the ArmDriver is shared with
the light robot via era_arm.robot.robot helpers, so there's a single source of truth.

Following LeRobot's "Bring Your Own Hardware" guide:
https://huggingface.co/docs/lerobot/integrate_hardware
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# lerobot is required to import this module (guarded by the `train` extra).
from lerobot.cameras import CameraConfig, make_cameras_from_configs
from lerobot.robots import Robot, RobotConfig

from era_arm.driver.arm import ArmDriver
from era_arm.driver.protocol import SERIAL_BAUD
from era_arm.robot.robot import MOTOR_KEYS, state_from_angles, targets_from_action


@RobotConfig.register_subclass("era_arm")
@dataclass
class EraArmRobotConfig(RobotConfig):
    port: str = "/dev/era-arm"          # serial port of the ESP32
    baud: int = SERIAL_BAUD
    clamp: bool = False                  # clamp out-of-range targets instead of raising
    cameras: dict[str, CameraConfig] = field(default_factory=dict)


class LeRobotEraArm(Robot):
    """era-arm as a first-class LeRobot Robot (flat '<joint>.pos' dicts + cameras)."""

    config_class = EraArmRobotConfig
    name = "era_arm"

    def __init__(self, config: EraArmRobotConfig):
        super().__init__(config)
        self.config = config
        self.driver: ArmDriver | None = None
        self.cameras = make_cameras_from_configs(config.cameras)

    # --- feature contract ------------------------------------------------------

    @property
    def _motors_ft(self) -> dict:
        return {key: float for key in MOTOR_KEYS}

    @property
    def _cameras_ft(self) -> dict:
        return {name: (cam.height, cam.width, 3) for name, cam in self.cameras.items()}

    @property
    def observation_features(self) -> dict:
        return {**self._motors_ft, **self._cameras_ft}

    @property
    def action_features(self) -> dict:
        return dict(self._motors_ft)

    # --- status ----------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self.driver is not None and all(c.is_connected for c in self.cameras.values())

    @property
    def is_calibrated(self) -> bool:
        return True  # encoder zero-offsets are calibrated in firmware

    # --- lifecycle -------------------------------------------------------------

    def connect(self, calibrate: bool = True) -> None:
        self.driver = ArmDriver.open(self.config.port, baud=self.config.baud, clamp=self.config.clamp)
        for cam in self.cameras.values():
            cam.connect()
        self.configure()

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def disconnect(self) -> None:
        if self.driver is not None:
            self.driver.close()
            self.driver = None
        for cam in self.cameras.values():
            cam.disconnect()

    # --- runtime I/O -----------------------------------------------------------

    def get_observation(self) -> dict[str, Any]:
        if not self.is_connected:
            raise ConnectionError(f"{self} is not connected.")
        obs = state_from_angles(self.driver.read_state().angles)
        for cam_key, cam in self.cameras.items():
            obs[cam_key] = cam.async_read()
        return obs

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if not self.is_connected:
            raise ConnectionError(f"{self} is not connected.")
        self.driver.send_targets(targets_from_action(action))
        return action
