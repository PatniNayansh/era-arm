"""Tests for ArmDriver, exercised end-to-end against the FakeArm mock."""

import pytest

from era_arm.driver.arm import ArmDriver
from era_arm.driver.mock import FakeArm


def test_send_then_read_roundtrip():
    arm = ArmDriver(FakeArm())
    arm.send_targets([10, 20, 0, 0, 90, 45])
    assert arm.read_state().angles == [10.0, 20.0, 0.0, 0.0, 90.0, 45.0]


def test_read_state_returns_latest_of_many_buffered():
    # Simulate the real arm streaming several ticks; read_state must return the
    # freshest pose, not the first stale one sitting in the buffer.
    fake = FakeArm()
    fake.angles = [1, 1, 1, 1, 1, 1]
    fake.emit_status()
    fake.angles = [2, 2, 2, 2, 2, 2]
    fake.emit_status()
    fake.angles = [3, 3, 3, 3, 3, 3]
    fake.emit_status()

    arm = ArmDriver(fake)
    assert arm.read_state().angles == [3.0, 3.0, 3.0, 3.0, 3.0, 3.0]


def test_read_state_blocks_for_a_line_when_buffer_empty():
    # Empty buffer: FakeArm streams a fresh line rather than hanging.
    arm = ArmDriver(FakeArm())
    assert arm.read_state().angles == [0.0] * 6


def test_out_of_range_raises_by_default():
    arm = ArmDriver(FakeArm())
    with pytest.raises(ValueError):
        arm.send_targets([0, 200, 0, 0, 90, 45])


def test_clamp_mode_sends_nearest_safe_pose():
    arm = ArmDriver(FakeArm(), clamp=True)
    arm.send_targets([0, 200, 0, 0, 90, 45])  # 200 clamps to shoulder max (90)
    assert arm.read_state().angles == [0.0, 90.0, 0.0, 0.0, 90.0, 45.0]


def test_context_manager_closes_connection():
    fake = FakeArm()
    closed = {"value": False}
    fake.close = lambda: closed.__setitem__("value", True)
    with ArmDriver(fake) as arm:
        arm.send_targets([0, 0, 0, 0, 90, 0])
    assert closed["value"] is True
