# Layer 5 — Train (`era_arm/train`)

Trains policies on recorded demonstrations using **LeRobot**. This layer is a thin,
honest wrapper around LeRobot's own training CLI so we don't couple to its
fast-changing Python API.

## Requirements (not installed by default)

Training needs LeRobot + PyTorch + a CUDA GPU (the RTX 5070 box, native Ubuntu).
Install the extra there:

```
uv sync --extra train
```

Under WSL / no GPU, use `--dry-run` to see the exact command that would run.

## Policy roadmap (see docs/decisions.md)

1. **ACT** — mandatory baseline and the month-3 gate: must reach **≥40% success**
   before any VLA work. See `configs/act.md`.
2. **SmolVLA** — first VLA step.
3. **GR00T-N1.5** — primary target for best documented results on cheap arms.

## Usage

```
# Show the command without running it (works anywhere):
uv run python -m era_arm.train.train --dataset PatniNayansh/era-arm-pick --policy act --dry-run

# Actually train (on the GPU box, after `uv sync --extra train`):
uv run python -m era_arm.train.train --dataset PatniNayansh/era-arm-pick --policy act \
    --steps 100000 --output outputs/act-pick
```

Any extra flags after the known ones are passed straight through to `lerobot-train`.

## Pipeline

record (L4) → convert episodes to a LeRobotDataset → **train (here)** → eval (L6).
The episode→LeRobotDataset conversion is the seam noted in
`era_arm/teleop/record.py`; wire it up once `lerobot` is installed.
