"""Layer 2 — the ArmDriver: the object the rest of the project uses to talk to the arm.

Everything above this layer (robot, teleop, ...) holds an ArmDriver and calls
.send_targets(...) / .read_state(). They never touch serial ports or the text
protocol directly — that's this file's job, built on protocol.py.
"""

from __future__ import annotations

from era_arm.driver.protocol import (
    SERIAL_BAUD,
    ArmState,
    clamp_targets,
    format_command,
    parse_status,
)


class ArmDriver:
    """Send target angles to the arm and read its status back.

    `connection` is anything with a pyserial-like surface: `write(bytes)`,
    `readline() -> bytes`, and `in_waiting`. In production that's a
    `serial.Serial`; in tests it's a `FakeArm` from mock.py. Passing it in
    (rather than opening a port inside here) is what lets the same driver run
    against both — see the `open()` classmethod for the real-hardware path.

    If `clamp` is True, out-of-range targets are pulled to the nearest safe
    value instead of raising; if False (default), an out-of-range target raises.
    """

    def __init__(self, connection, clamp: bool = False):
        self._conn = connection
        self._clamp = clamp

    def send_targets(self, targets) -> None:
        """Send six target joint angles (degrees) to the arm."""
        targets = list(targets)
        if self._clamp:
            targets = clamp_targets(targets)
        self._conn.write(format_command(targets))

    def read_state(self) -> ArmState:
        """Return the arm's most recent status.

        The firmware streams status continuously, so several lines may be waiting.
        We drain everything buffered and keep the freshest valid line — that's the
        one reflecting the arm's true current pose. Garbled/partial lines (which
        happen on real serial) are skipped rather than crashing the read.
        """
        latest = None
        while getattr(self._conn, "in_waiting", 0):
            try:
                latest = parse_status(self._conn.readline())
            except ValueError:
                continue  # skip a partial or corrupted line, keep draining
        if latest is None:
            # Nothing buffered yet — block for the next line the arm sends.
            latest = parse_status(self._conn.readline())
        return latest

    def close(self) -> None:
        """Close the underlying connection, if it has a close()."""
        close = getattr(self._conn, "close", None)
        if callable(close):
            close()

    # Context-manager support, so callers can write:
    #     with ArmDriver.open("/dev/ttyUSB0") as arm:
    #         arm.send_targets(...)
    # and the port is closed automatically on the way out, even on error.
    def __enter__(self) -> "ArmDriver":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @classmethod
    def open(cls, port, baud: int = SERIAL_BAUD, timeout: float = 1.0, clamp: bool = False):
        """Open a REAL serial port and wrap it in an ArmDriver.

        Example (once hardware is connected):
            with ArmDriver.open("/dev/ttyUSB0") as arm:
                arm.send_targets([0, 0, 0, 0, 90, 0])
                print(arm.read_state().angles)

        `serial` is pyserial; `timeout` caps how long a single readline() blocks.
        """
        import serial  # imported lazily so tests/mocks don't need a real port

        conn = serial.Serial(port, baud, timeout=timeout)
        return cls(conn, clamp=clamp)
