import pytest

from era_arm.driver.protocol import NUM_JOINTS, encode_command, parse_status


def test_encode_command_formats_six_joints():
    targets = [10.0, -5.5, 0.0, 180.0, 90.25, 45.0]
    assert encode_command(targets) == b"P,10.00,-5.50,0.00,180.00,90.25,45.00\n"


def test_encode_command_rejects_wrong_joint_count():
    with pytest.raises(ValueError):
        encode_command([0.0] * (NUM_JOINTS - 1))


def test_parse_status_round_trips_firmware_line():
    line = "S,10.00,-5.50,0.00,180.00,90.25,45.00,123456,0\n"
    status = parse_status(line)
    assert status.position_deg == [10.0, -5.5, 0.0, 180.0, 90.25, 45.0]
    assert status.timestamp_ms == 123456
    assert status.watchdog_tripped is False


def test_parse_status_detects_watchdog_tripped():
    status = parse_status("S,0,0,0,0,0,0,999,1")
    assert status.watchdog_tripped is True


def test_parse_status_rejects_malformed_line():
    with pytest.raises(ValueError):
        parse_status("garbage\n")
