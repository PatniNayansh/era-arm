# E.R.A. — a low-cost 6-DOF robot arm that learns by imitation

`era-arm` is a 6-joint robot arm plus the software to teach it tasks from
demonstration: teleoperate the arm → record demos → train a policy (ACT → SmolVLA
→ GR00T) → run the policy on the arm. Built bottom-up as six layers, each usable
and tested on its own.

## Architecture (six layers)

| Layer | Package | Role | Status |
|---|---|---|---|
| **L1** firmware | `firmware/` | ESP32-S3: drives 4 steppers + 2 servos, reads 5 AS5600 encoders, 50 Hz loop | scaffold (compiles; not flashed) |
| **L2** driver | `era_arm/driver/` | Python serial link to the ESP32 (protocol, `ArmDriver`) | complete, tested |
| **L3** robot | `era_arm/robot/` | arm + cameras → one observation/action interface | complete, tested |
| **L4** teleop | `era_arm/teleop/` | drive the arm, record demonstrations | complete, tested |
| **L5** train | `era_arm/train/` | train policies via LeRobot | CLI wrapper (needs GPU) |
| **L6** eval | `era_arm/eval/` | run a trained policy on the arm | complete, tested |

Each layer has its own README with details; design rationale lives in
[`docs/decisions.md`](docs/decisions.md).

## Quickstart

```bash
./setup.sh                 # system deps + uv + pinned Python 3.12 (first time)
uv sync                    # create the project environment
uv run pytest              # run the full test suite
```

Try the layers with **no hardware** (everything runs against mocks):

```bash
uv run python -m era_arm.driver.demo        # L2: send poses, read state
uv run python -m era_arm.teleop.demo_record # L4: record an episode
uv run python -m era_arm.eval.demo_rollout  # L6: run a policy rollout
uv run python -m era_arm.train.train --dataset demo --dry-run  # L5: show the train command
```

## Optional extras (per machine)

Heavy/hardware deps are opt-in to keep the core light:

```bash
uv sync --extra camera   # OpenCV, for real USB cameras (native Ubuntu)
uv sync --extra teleop   # pynput, for keyboard teleop
uv sync --extra train    # LeRobot + torch, on the CUDA GPU box
```

## Real ML workflow (LeRobot)

The stack conforms to LeRobot's `Robot` interface: `EraArmRobot` uses flat
`{"<joint>.pos": ...}` observation/action dicts, and `LeRobotEraArm`
(`era_arm/robot/lerobot_robot.py`) is a registered `Robot` subclass, so LeRobot's
CLIs drive the physical arm end-to-end:

```bash
uv sync --extra train                                            # LeRobot + torch (GPU box)

lerobot-teleoperate --robot.type=era_arm --robot.port=/dev/era-arm ...      # drive it
lerobot-record      --robot.type=era_arm --robot.port=/dev/era-arm \        # collect demos
                    --dataset.repo_id=you/era-arm-pick --dataset.num_episodes=30
uv run python -m era_arm.train.train --dataset you/era-arm-pick --policy act # train ACT
uv run python -m era_arm.eval.evaluate --checkpoint outputs/.../last \       # run on arm
                    --port /dev/era-arm --dataset you/era-arm-eval
```

The Python layers (`teleop`/`train`/`eval`) wrap these commands and add mock-testable
loops for offline development. See each layer's README for details.

## Going to real hardware

The software is built and tested against mocks. To run on the physical arm:
flash the firmware, then swap the mock for real I/O — `ArmDriver.open("/dev/era-arm")`
instead of `FakeArm()`, and `OpenCVCamera(...)` instead of `MockCamera()`. Calibrate
joint limits (`era_arm/driver/protocol.py`) and encoder offsets
(`scripts/calibrate.py`) once wired. See `docs/decisions.md` for the WSL→native-Ubuntu
plan (USB cameras need native Ubuntu).
