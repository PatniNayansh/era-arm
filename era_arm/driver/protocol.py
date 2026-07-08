"""Encode/parse the serial line protocol spoken by firmware/src/serial_protocol.cpp.

Host -> MCU:  "P,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>\\n"   target angles, degrees
MCU  -> Host: "S,<j0>,<j1>,<j2>,<j3>,<j4>,<j5>,<millis>,<watchdog>\\n"
"""

from dataclasses import dataclass

NUM_JOINTS = 6


def encode_command(target_deg: list[float]) -> bytes:
    if len(target_deg) != NUM_JOINTS:
        raise ValueError(f"expected {NUM_JOINTS} joint targets, got {len(target_deg)}")
    fields = ",".join(f"{deg:.2f}" for deg in target_deg)
    return f"P,{fields}\n".encode("ascii")


@dataclass
class ArmStatus:
    position_deg: list[float]
    timestamp_ms: int
    watchdog_tripped: bool


def parse_status(line: str) -> ArmStatus:
    parts = line.strip().split(",")
    if len(parts) != NUM_JOINTS + 3 or parts[0] != "S":
        raise ValueError(f"malformed status line: {line!r}")

    position_deg = [float(p) for p in parts[1 : 1 + NUM_JOINTS]]
    timestamp_ms = int(parts[1 + NUM_JOINTS])
    watchdog_tripped = parts[2 + NUM_JOINTS] == "1"
    return ArmStatus(position_deg=position_deg, timestamp_ms=timestamp_ms, watchdog_tripped=watchdog_tripped)
