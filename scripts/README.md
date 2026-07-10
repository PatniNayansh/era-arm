# Scripts

Standalone utilities.

- `99-era-arm.rules` — udev rule for a stable `/dev/era-arm` device name. Edit the
  vendor/product ids to match your board, then
  `sudo cp scripts/99-era-arm.rules /etc/udev/rules.d/ && sudo udevadm control --reload-rules && sudo udevadm trigger`.
- `replay_test.py` — replays a recorded episode's actions on the arm to validate
  data before training. Runs against the mock by default:
  `uv run python scripts/replay_test.py datasets/episode_000.npz [--port /dev/era-arm]`.
- `calibrate.py` — reads encoder zero-offsets from the real arm (hardware only):
  `uv run python scripts/calibrate.py --port /dev/era-arm`.

The `replay_actions` / `load_actions` helpers in `replay_test.py` are covered by
`tests/test_scripts.py`.
