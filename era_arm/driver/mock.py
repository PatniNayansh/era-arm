"""A fake ESP32 for testing Layer 2 without any hardware plugged in.

The real Layer 1 firmware lives on a physical chip at the end of a USB cable.
Until that's wired up, this class *pretends to be* that chip in pure Python. It
mimics just enough of pyserial's interface — `write`, `readline`, `in_waiting`,
`reset_input_buffer`, `close` — that ArmDriver can't tell it apart from a real port.

Unlike a naive mock, this one models the important real-hardware behaviour: the
firmware streams a status line every control tick (~50 Hz) whether or not you
just sent a command. So status lines pile up in an outgoing buffer, and the
driver has to cope with reading the *latest* one.
"""

from __future__ import annotations

from era_arm.driver.protocol import NUM_JOINTS


class FakeArm:
    def __init__(self):
        # Where the pretend arm currently is. Starts folded up at all zeros.
        self.angles = [0.0] * NUM_JOINTS
        self._clock_ms = 0            # a fake millis() clock, like the ESP32's
        self._rx = bytearray()        # bytes queued up for the host to read

    # --- pyserial-look-alike surface -------------------------------------------

    @property
    def in_waiting(self):
        """Number of bytes waiting to be read — pyserial exposes this too."""
        return len(self._rx)

    def write(self, data):
        """The driver calls this to SEND a command to us (the 'firmware')."""
        parts = data.decode("ascii").strip().split(",")
        # A real arm eases toward its target; our fake one teleports there.
        self.angles = [float(p) for p in parts[1 : 1 + NUM_JOINTS]]
        # The firmware would emit a status the very next tick — model that.
        self.emit_status()
        return len(data)

    def readline(self):
        """The driver calls this to READ one status line (bytes)."""
        if not self._rx:
            # Nothing queued — the real arm would still be streaming, so do too.
            self.emit_status()
        newline = self._rx.find(b"\n")
        if newline == -1:
            line = bytes(self._rx)
            self._rx.clear()
        else:
            line = bytes(self._rx[: newline + 1])
            del self._rx[: newline + 1]
        return line

    def reset_input_buffer(self):
        """Throw away everything queued — pyserial has this too."""
        self._rx.clear()

    def close(self):
        pass

    # --- test/helper surface ---------------------------------------------------

    def emit_status(self, watchdog=False):
        """Queue one status line reflecting the current pose (one 50 Hz tick)."""
        self._clock_ms += 20
        body = ",".join(f"{a:.1f}" for a in self.angles)
        flag = "1" if watchdog else "0"
        self._rx.extend(f"S,{body},{self._clock_ms},{flag}\n".encode("ascii"))
