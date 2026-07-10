"""Layer 5 — training entry point.

We train policies with LeRobot. Rather than depend on lerobot's fast-moving Python
API, this is an honest thin wrapper: it builds the exact `lerobot-train` command
from a few arguments and runs it via subprocess (or just prints it with --dry-run).

`build_train_command()` is a pure function so it's unit-testable without lerobot,
torch, or a GPU installed. Running the command for real needs the `train` extra
(`uv sync --extra train`) and a CUDA GPU — see README.md.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

# Per docs/decisions.md: ACT is the mandatory baseline + month-3 gate, then SmolVLA,
# then GR00T-N1.5. Keep this list in sync with the decision log.
SUPPORTED_POLICIES = ("act", "smolvla", "gr00t")


def build_train_command(dataset: str, policy: str = "act", output: str = "outputs/train",
                        steps: int = 100_000, batch_size: int = 8, extra=None) -> list:
    """Return the argv list for `lerobot-train` given our high-level options."""
    if policy not in SUPPORTED_POLICIES:
        raise ValueError(f"unknown policy {policy!r}; expected one of {SUPPORTED_POLICIES}")
    cmd = [
        "lerobot-train",
        f"--policy.type={policy}",
        f"--dataset.repo_id={dataset}",
        f"--output_dir={output}",
        f"--steps={steps}",
        f"--batch_size={batch_size}",
    ]
    if extra:
        cmd.extend(extra)
    return cmd


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Train an era-arm policy via LeRobot.")
    parser.add_argument("--dataset", required=True, help="LeRobotDataset repo_id or local path")
    parser.add_argument("--policy", default="act", choices=SUPPORTED_POLICIES)
    parser.add_argument("--output", default="outputs/train")
    parser.add_argument("--steps", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true", help="print the command, don't run it")
    parser.add_argument("extra", nargs="*", help="extra flags passed through to lerobot-train")
    args = parser.parse_args(argv)

    cmd = build_train_command(
        dataset=args.dataset, policy=args.policy, output=args.output,
        steps=args.steps, batch_size=args.batch_size, extra=args.extra,
    )
    print("+ " + " ".join(cmd))
    if args.dry_run:
        return 0

    if shutil.which("lerobot-train") is None:
        print(
            "error: 'lerobot-train' not found. Install the training extra on a CUDA "
            "machine:\n    uv sync --extra train\nThen re-run (or use --dry-run here).",
            file=sys.stderr,
        )
        return 1
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
