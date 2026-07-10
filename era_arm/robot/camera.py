"""Layer 3 — camera sources for the robot's visual observations.

A camera is anything with connect() / read() -> RGB frame / disconnect(). We keep
a pure-Python `MockCamera` (deterministic synthetic frames, no hardware) for
building and testing everything today, and an `OpenCVCamera` that reads a real USB
webcam via OpenCV. cv2 is imported lazily so the package works without it installed
(and note: USB cameras don't work under WSL yet — see docs/decisions.md).
"""

from __future__ import annotations

import numpy as np


class MockCamera:
    """A fake camera that returns deterministic synthetic frames.

    Each frame is a solid image whose brightness advances by one per read, so
    successive frames differ — enough to exercise the recording/observation
    plumbing without any hardware.
    """

    def __init__(self, width: int = 320, height: int = 240, name: str = "mock"):
        self.width = width
        self.height = height
        self.name = name
        self._frame = 0
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def read(self) -> np.ndarray:
        """Return one (height, width, 3) uint8 RGB frame."""
        value = self._frame % 256
        self._frame += 1
        return np.full((self.height, self.width, 3), value, dtype=np.uint8)

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


class OpenCVCamera:
    """A real USB webcam read through OpenCV.

    Not usable under WSL (no USB camera passthrough); intended for native Ubuntu.
    `cv2` is imported inside the methods so importing this module never requires
    OpenCV to be installed.
    """

    def __init__(self, index: int = 0, width: int = 640, height: int = 480, name: str = "cam"):
        self.index = index
        self.width = width
        self.height = height
        self.name = name
        self._cap = None

    def connect(self) -> None:
        import cv2  # lazy: only needed on real hardware

        self._cap = cv2.VideoCapture(self.index)
        if not self._cap.isOpened():
            raise RuntimeError(f"could not open camera index {self.index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self) -> np.ndarray:
        import cv2

        if self._cap is None:
            raise RuntimeError("camera not connected; call connect() first")
        ok, frame = self._cap.read()
        if not ok:
            raise RuntimeError(f"failed to read frame from camera {self.index}")
        # OpenCV returns BGR; the rest of the stack expects RGB.
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def disconnect(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def is_connected(self) -> bool:
        return self._cap is not None
