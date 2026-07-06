# Decision Log

Format: what we decided, why, and when to revisit.

## Ubuntu 24.04 LTS (not 22.04 or 26.04)
22.04 too old for the RTX 5070 (Blackwell/sm_120) stack; 26.04 too new (ecosystem
not caught up). 24.04 = mature, ships Python 3.12 natively, and every RTX-50 guide
targets it. Both machines standardized on it.

## Python 3.12 (not 3.14)
PyTorch has no CUDA wheels for 3.14 yet (installs CPU-only), and LeRobot targets
3.12/3.13. Pinned via uv so the system Python version is irrelevant.

## ffmpeg 7 with libsvtav1 (not 8)
LeRobot's dataset format encodes video with libsvtav1; ffmpeg 8 can be too new for
the TorchCodec decoder. 7.x is the known-good version.

## WSL2 now, dual-boot native Ubuntu by ~month 2
WSL2 is fine for env setup + firmware/serial, but can't do USB cameras without
recompiling the kernel. Native Ubuntu needed before the camera/teleop phase.

## Models: ACT → SmolVLA → GR00T-N1.5 (primary) → GR00T-N1.7 (stretch)
ACT is the mandatory baseline + month-3 gate (must hit >=40% before any VLA work).
GR00T-N1.5 primary for best documented results on cheap arms. Settled — not revisiting.

## uv for environment management
Pins the project's own Python + dependencies, isolated from the system.
