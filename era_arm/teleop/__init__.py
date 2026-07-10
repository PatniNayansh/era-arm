"""Layer 4 — teleop: drive the arm to collect demonstrations.

KeyboardTeleop is intentionally NOT imported here (it needs the optional `pynput`
extra); import it explicitly with `from era_arm.teleop.keyboard import KeyboardTeleop`.
"""

from era_arm.teleop.base import Teleoperator
from era_arm.teleop.record import Episode, record_episode, save_episode
from era_arm.teleop.scripted import ScriptedTeleop

__all__ = ["Teleoperator", "ScriptedTeleop", "Episode", "record_episode", "save_episode"]
