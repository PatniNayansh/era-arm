# ACT — Action Chunking Transformer (baseline policy)

ACT is the mandatory baseline and the **month-3 gate**: it must reach **≥40%
success** on the target task before any VLA work (SmolVLA / GR00T) begins
(docs/decisions.md).

## Starting hyperparameters

These are LeRobot's ACT defaults with arm-specific notes; tune from here.

| Param | Value | Note |
|---|---|---|
| `--policy.type` | `act` | |
| `--policy.chunk_size` | 100 | actions predicted per forward pass |
| `--policy.n_action_steps` | 100 | actions executed before re-planning |
| `--steps` | 100000 | ~a few hours on the RTX 5070 |
| `--batch_size` | 8 | raise if VRAM allows |
| observations | `joints` (6) + one or more `image.<name>` | must match how episodes were recorded (Layer 3/4) |
| action | `joints` (6 target angles, degrees) | |

## Command

```
uv run python -m era_arm.train.train \
    --dataset <repo_id_or_path> --policy act \
    --steps 100000 --batch-size 8 --output outputs/act-<task>
```

Add pass-through flags after the known ones, e.g.
`... -- --policy.chunk_size=50`.
