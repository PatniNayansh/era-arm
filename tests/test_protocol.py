"""Tests for the Layer 2 serial protocol — pure text/number rules, no hardware."""

import math

import pytest

from era_arm.driver.protocol import (
    NUM_JOINTS,
    ArmState,
    clamp_targets,
    format_command,
    parse_status,
    validate_targets,
)


# --- format_command ------------------------------------------------------------

def test_format_command_basic():
    assert format_command([10, 20, 0, 0, 90, 45]) == b"P,10,20,0,0,90,45\n"


def test_format_command_keeps_decimals_compact():
    # 45.5 stays "45.5"; 90.0 collapses to "90".
    assert format_command([0, 0, 0, 0, 90.0, 45.5]) == b"P,0,0,0,0,90,45.5\n"


def test_format_command_wrong_length_raises():
    with pytest.raises(ValueError):
        format_command([0, 0, 0])


def test_format_command_out_of_range_raises():
    # J1 (shoulder) limit is [-90, 90]; 200 is out of range.
    with pytest.raises(ValueError):
        format_command([0, 200, 0, 0, 90, 45])


def test_format_command_non_finite_raises():
    with pytest.raises(ValueError):
        format_command([0, 0, 0, 0, 90, math.inf])


# --- validate / clamp ----------------------------------------------------------

def test_validate_targets_accepts_in_range():
    validate_targets([0, 0, 0, 0, 90, 45])  # should not raise


def test_clamp_targets_pulls_into_range():
    # base clamps to +180, shoulder to -90, gripper to +180.
    assert clamp_targets([999, -999, 0, 0, 90, 999]) == [180.0, -90.0, 0.0, 0.0, 90.0, 180.0]


# --- parse_status --------------------------------------------------------------

def test_parse_status_basic():
    state = parse_status(b"S,10.1,19.8,0.0,0.0,90.0,45.0,12345,1\n")
    assert isinstance(state, ArmState)
    assert state.angles == [10.1, 19.8, 0.0, 0.0, 90.0, 45.0]
    assert state.millis == 12345
    assert state.watchdog is True


def test_parse_status_watchdog_false():
    assert parse_status(b"S,0,0,0,0,0,0,7,0\n").watchdog is False


def test_parse_status_accepts_text_not_only_bytes():
    assert parse_status("S,0,0,0,0,0,0,7,0").angles == [0.0] * NUM_JOINTS


@pytest.mark.parametrize(
    "line",
    [
        b"P,0,0,0,0,0,0\n",           # wrong prefix
        b"S,0,0,0\n",                  # too few fields
        b"S,0,0,0,0,0,0,0,0,0,0\n",    # too many fields
        b"S,x,0,0,0,0,0,7,0\n",        # non-numeric angle
        b"\n",                          # empty
    ],
)
def test_parse_status_rejects_malformed(line):
    with pytest.raises(ValueError):
        parse_status(line)
