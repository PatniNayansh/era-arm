"""Layer 2 — the serial 'language' spoken between Python and the ESP32.

This module has NO hardware in it. It only knows the *text rules* of the protocol
and the arm's joint limits, so it can be tested without an arm plugged in:

    Host -> MCU:  "P,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>\n"          target angles, degrees
    MCU  -> Host: "S,<j0>,...,<j5>,<millis>,<watchdog>\n"      status, degrees
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

# The arm has 6 joints (J0-J5), so every command / status carries 6 angles.
NUM_JOINTS = 6

# Serial line speed the firmware expects (see firmware/include/config.h).
SERIAL_BAUD = 115200

# Human-readable joint names, index-aligned with J0..J5.
JOINT_NAMES = ("base", "shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper")

# Per-joint software safety limits, in output-shaft degrees, as (min, max).
# PLACEHOLDER RANGES — these must be measured/calibrated on the real arm and then
# recorded in docs/decisions.md. The servos (J4, J5) use the 0-180 range the
# firmware's ServoJointConfig assumes; the stepper ranges are conservative guesses.
JOINT_LIMITS_DEG = (
    (-180.0, 180.0),  # J0 base
    (-90.0, 90.0),    # J1 shoulder
    (-135.0, 135.0),  # J2 elbow
    (-90.0, 90.0),    # J3 wrist pitch
    (0.0, 180.0),     # J4 wrist roll (servo)
    (0.0, 180.0),     # J5 gripper (servo)
)


@dataclass
class ArmState:
    """One decoded status reply from the arm."""

    angles: list      # 6 measured joint angles, degrees
    millis: int       # the arm's own clock, in milliseconds
    watchdog: bool    # True == arm has stopped for safety (no recent command)


def _check_length(values, what):
    if len(values) != NUM_JOINTS:
        raise ValueError(f"expected {NUM_JOINTS} {what}, got {len(values)}")


def validate_targets(targets):
    """Raise ValueError unless `targets` is 6 finite angles within joint limits."""
    _check_length(targets, "angles")
    for i, angle in enumerate(targets):
        if not isfinite(angle):
            raise ValueError(f"joint {i} ({JOINT_NAMES[i]}) angle is not finite: {angle!r}")
        low, high = JOINT_LIMITS_DEG[i]
        if not (low <= angle <= high):
            raise ValueError(
                f"joint {i} ({JOINT_NAMES[i]}) angle {angle} out of range [{low}, {high}]"
            )


def clamp_targets(targets):
    """Return a copy of `targets` with each angle pulled inside its joint limits.

    Use this when a slightly-out-of-range command should be nudged to the nearest
    safe value instead of rejected outright.
    """
    _check_length(targets, "angles")
    clamped = []
    for angle, (low, high) in zip(targets, JOINT_LIMITS_DEG):
        clamped.append(min(high, max(low, float(angle))))
    return clamped


def format_command(targets):
    """Turn 6 target angles into the exact bytes to send over the wire.

    `targets` -> e.g. [10, 20, 0, 0, 90, 45]  ==>  b"P,10,20,0,0,90,45\n".
    Angles are validated against the joint limits first; raises ValueError if
    they're the wrong count, non-finite, or out of range.
    """
    validate_targets(targets)
    # `:g` keeps the text compact: 10.0 -> "10", 45.5 -> "45.5".
    body = ",".join(f"{float(a):g}" for a in targets)
    return f"P,{body}\n".encode("ascii")


def parse_status(raw):
    """Turn one raw status line from the arm into an ArmState.

    `raw` is the bytes read off the wire, e.g.
        b"S,10.1,19.8,0.0,0.0,90.0,45.0,12345,1\n"
    Raises ValueError on anything malformed (wrong prefix, wrong field count, or
    a field that isn't a number) so callers can skip garbled/partial lines.
    """
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("ascii", errors="replace")
    text = raw.strip()

    parts = text.split(",")
    # A valid status is "S" + 6 angles + millis + watchdog = NUM_JOINTS + 3 fields.
    if not parts or parts[0] != "S":
        raise ValueError(f"not a status line: {text!r}")
    if len(parts) != NUM_JOINTS + 3:
        raise ValueError(f"expected {NUM_JOINTS + 3} fields, got {len(parts)}: {text!r}")

    try:
        angles = [float(p) for p in parts[1 : 1 + NUM_JOINTS]]
        millis = int(parts[1 + NUM_JOINTS])
    except ValueError as exc:
        raise ValueError(f"non-numeric field in status: {text!r}") from exc

    watchdog = parts[-1] == "1"
    return ArmState(angles=angles, millis=millis, watchdog=watchdog)
