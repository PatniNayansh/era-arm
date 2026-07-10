"""Layer 3 — EraArmRobot: the arm + its cameras as one LeRobot-shaped robot.

This matches LeRobot's `Robot` interface exactly, but *duck-typed* — it does not
import lerobot, so the core stays light and mock-testable. Observations and actions
are flat dicts keyed the LeRobot way:

    observation = {"base.pos": 10.0, ..., "gripper.pos": 45.0, "top": <HxWx3 frame>}
    action      = {"base.pos": 10.0, ..., "gripper.pos": 45.0}

A real, CLI-discoverable `lerobot.robots.Robot` subclass built on the same driver
lives in `lerobot_robot.py` (guarded; only importable when lerobot is installed).
See docs/decisions.md and era_arm/robot/README.md.
"""

from __future__ import annotations

from era_arm.driver.arm import ArmDriver
from era_arm.driver.protocol import JOINT_NAMES, NUM_JOINTS

# LeRobot keys each motor's position as "<motor>.pos". These are our feature keys.
MOTOR_KEYS = tuple(f"{name}.pos" for name in JOINT_NAMES)


def action_from_targets(targets) -> dict:
    """[10, 20, ...] -> {"base.pos": 10.0, "shoulder.pos": 20.0, ...} (LeRobot action)."""
    if len(targets) != NUM_JOINTS:
        raise ValueError(f"expected {NUM_JOINTS} targets, got {len(targets)}")
    return {key: float(v) for key, v in zip(MOTOR_KEYS, targets)}


def targets_from_action(action: dict) -> list:
    """{"base.pos": 10.0, ...} -> [10.0, 20.0, ...] in J0..J5 order."""
    try:
        return [float(action[key]) for key in MOTOR_KEYS]
    except KeyError as exc:
        raise ValueError(f"action missing joint key {exc}; need {list(MOTOR_KEYS)}") from exc


def state_from_angles(angles) -> dict:
    """[10.0, 20.0, ...] -> {"base.pos": 10.0, ...} (motor part of an observation)."""
    return {key: float(v) for key, v in zip(MOTOR_KEYS, angles)}


class EraArmRobot:
    """A 6-joint arm plus named cameras, exposing LeRobot's Robot interface.

    `driver` is a Layer 2 ArmDriver (real or FakeArm-backed). `cameras` maps a
    camera name -> camera object (MockCamera / OpenCVCamera); None for no cameras.
    The safety watchdog isn't a policy feature, so it's kept off the observation
    dict and exposed via `last_watchdog` / `read_watchdog()`.
    """

    name = "era_arm"

    def __init__(self, driver: ArmDriver, cameras: dict | None = None):
        self.driver = driver
        self.cameras = dict(cameras) if cameras else {}
        self._connected = False
        self.last_watchdog = False

    # --- status ----------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_calibrated(self) -> bool:
        # Encoder zero-offsets are calibrated in firmware; nothing to do host-side.
        return True

    # --- feature contract (must work even when disconnected) -------------------

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

    # --- lifecycle -------------------------------------------------------------

    def connect(self, calibrate: bool = True) -> None:
        for cam in self.cameras.values():
            cam.connect()
        self._connected = True

    def configure(self) -> None:
        pass

    def calibrate(self) -> None:
        pass

    def disconnect(self) -> None:
        for cam in self.cameras.values():
            cam.disconnect()
        self.driver.close()
        self._connected = False

    # --- runtime I/O -----------------------------------------------------------

    def get_observation(self) -> dict:
        """Read joints + cameras into a flat LeRobot observation dict."""
        if not self._connected:
            raise ConnectionError("robot not connected; call connect() first")
        state = self.driver.read_state()
        self.last_watchdog = state.watchdog
        obs = state_from_angles(state.angles)
        for name, cam in self.cameras.items():
            obs[name] = cam.read()
        return obs

    def send_action(self, action: dict) -> dict:
        """Send a flat LeRobot action dict; returns the action actually sent."""
        if not self._connected:
            raise ConnectionError("robot not connected; call connect() first")
        self.driver.send_targets(targets_from_action(action))
        return action

    def read_watchdog(self) -> bool:
        """Convenience: the safety-watchdog flag from the last status read."""
        return self.last_watchdog

    def __enter__(self) -> "EraArmRobot":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.disconnect()
