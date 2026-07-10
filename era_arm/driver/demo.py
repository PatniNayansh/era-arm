"""A tiny end-to-end demo of Layer 2, driven by the FakeArm — no hardware needed.

Run it with:   uv run python -m era_arm.driver.demo

The only line that changes when the real arm is plugged in is the one marked
below: swap FakeArm() for ArmDriver.open("/dev/ttyUSB0").
"""

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm

# A little sequence of poses to run through, one per "step".
POSES = [
    [0, 0, 0, 0, 90, 0],
    [10, 20, 0, 0, 90, 45],
    [-30, -10, 45, 15, 0, 90],
]


def main():
    # Build the driver around a fake arm. (Later: ArmDriver.open("/dev/ttyUSB0"))
    arm = ArmDriver(FakeArm())

    print("start: ", arm.read_state().angles)
    for pose in POSES:
        arm.send_targets(pose)         # command a pose
        state = arm.read_state()        # read back where the arm now is
        print(f"sent {pose} -> arm at {state.angles}  (watchdog={state.watchdog})")


# Runs main() only when you execute the file directly, not when it's imported.
if __name__ == "__main__":
    main()
