"""Talks to the ESP32-S3 firmware (firmware/src/main.cpp) over USB serial."""

import serial

from era_arm.driver.protocol import ArmStatus, encode_command, parse_status

DEFAULT_BAUD = 115200


class SerialArmDriver:
    def __init__(self, port: str, baud: int = DEFAULT_BAUD, timeout_s: float = 0.1):
        self.port = port
        self.baud = baud
        self.timeout_s = timeout_s
        self._serial: serial.Serial | None = None

    def connect(self) -> None:
        self._serial = serial.Serial(self.port, self.baud, timeout=self.timeout_s)

    def disconnect(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def __enter__(self) -> "SerialArmDriver":
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.disconnect()

    def send_positions(self, target_deg: list[float]) -> None:
        if self._serial is None:
            raise RuntimeError("not connected — call connect() first")
        self._serial.write(encode_command(target_deg))

    def read_status(self) -> ArmStatus | None:
        """Returns the latest status line, or None if none arrived within the timeout."""
        if self._serial is None:
            raise RuntimeError("not connected — call connect() first")
        line = self._serial.readline().decode("ascii", errors="ignore")
        if not line:
            return None
        return parse_status(line)
