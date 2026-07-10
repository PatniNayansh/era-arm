"""Layer 4 — KeyboardTeleop: nudge joints from the keyboard.

Real-use teleoperator (needs a terminal/display and the `pynput` extra:
`uv sync --extra teleop`). Not unit-tested here — it reads live key events.
`pynput` is imported lazily so importing this module never requires it.

Keys (default): pairs of keys step each joint up/down by `step_deg` degrees.
    q/a J0   w/s J1   e/d J2   r/f J3   t/g J4   y/h J5
Space re-centers all joints to the midpoint of their limits.
"""

from __future__ import annotations

from era_arm.driver.protocol import JOINT_LIMITS_DEG, NUM_JOINTS
from era_arm.robot import action_from_targets
from era_arm.teleop.base import Teleoperator

_UP_KEYS = "qwerty"     # J0..J5 increase
_DOWN_KEYS = "asdfgh"   # J0..J5 decrease


def _midpoints():
    return [(lo + hi) / 2.0 for lo, hi in JOINT_LIMITS_DEG]


class KeyboardTeleop(Teleoperator):
    def __init__(self, step_deg: float = 2.0):
        self.step_deg = step_deg
        self._targets = _midpoints()
        self._pressed = set()
        self._listener = None

    def start(self) -> None:
        from pynput import keyboard  # lazy: only needed for real teleop

        self._targets = _midpoints()

        def on_press(key):
            ch = getattr(key, "char", None)
            if ch:
                self._pressed.add(ch)
            if key == keyboard.Key.space:
                self._targets = _midpoints()

        def on_release(key):
            ch = getattr(key, "char", None)
            if ch:
                self._pressed.discard(ch)

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()

    def get_action(self):
        for j in range(NUM_JOINTS):
            if _UP_KEYS[j] in self._pressed:
                self._targets[j] += self.step_deg
            if _DOWN_KEYS[j] in self._pressed:
                self._targets[j] -= self.step_deg
            lo, hi = JOINT_LIMITS_DEG[j]
            self._targets[j] = min(hi, max(lo, self._targets[j]))
        return action_from_targets(self._targets)

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
