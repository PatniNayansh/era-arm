"""Encoder zero-offset calibration helper (hardware).

Each joint's AS5600 encoder reports a raw angle; the firmware/driver need to know
what raw reading corresponds to the joint's defined zero. This tool: you move the
arm to its zero pose by hand, then it reads the current joint angles and prints the
offsets to paste into firmware/include/config.h (JOINT_ENCODERS[].zeroOffsetDeg)
and, if used there too, era_arm/driver/protocol.py.

Requires the real arm + flashed firmware:
    uv run python scripts/calibrate.py --port /dev/era-arm

There is no mock path — calibration is inherently a hardware step. See
docs/decisions.md ("Position feedback: AS5600 magnetic encoders").
"""

from __future__ import annotations

import argparse

from era_arm.driver.arm import ArmDriver
from era_arm.driver.protocol import JOINT_NAMES


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read encoder zero-offsets from the arm.")
    parser.add_argument("--port", required=True, help="serial port, e.g. /dev/era-arm")
    parser.add_argument("--samples", type=int, default=20, help="readings to average")
    args = parser.parse_args(argv)

    print("Move the arm to its ZERO pose by hand, then press Enter...")
    input()

    with ArmDriver.open(args.port) as arm:
        acc = [0.0] * len(JOINT_NAMES)
        for _ in range(args.samples):
            angles = arm.read_state().angles
            acc = [a + b for a, b in zip(acc, angles)]
        offsets = [a / args.samples for a in acc]

    print("\nMeasured zero-offsets (degrees):")
    for name, off in zip(JOINT_NAMES, offsets):
        print(f"  {name:12s} {off:8.3f}")
    print("\nPaste these into firmware/include/config.h JOINT_ENCODERS[].zeroOffsetDeg,")
    print("then record the change in docs/decisions.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
