"""Generic USB webcam capture via OpenCV.

Assumes a plain UVC webcam (cv2.VideoCapture). If the arm ends up using a
depth camera (e.g. Intel RealSense) instead, swap this out for its SDK --
nothing above this layer depends on OpenCV specifically.
"""

import cv2
import numpy as np

DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 30


class Camera:
    def __init__(
        self,
        index: int = 0,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        fps: int = DEFAULT_FPS,
    ):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: cv2.VideoCapture | None = None

    def connect(self) -> None:
        cap = cv2.VideoCapture(self.index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        if not cap.isOpened():
            raise RuntimeError(f"could not open camera at index {self.index}")
        self._cap = cap

    def disconnect(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        self.connect()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.disconnect()

    def read_frame(self) -> np.ndarray:
        """Returns one RGB frame (height, width, 3)."""
        if self._cap is None:
            raise RuntimeError("not connected — call connect() first")
        ok, frame_bgr = self._cap.read()
        if not ok:
            raise RuntimeError("failed to read frame from camera")
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
