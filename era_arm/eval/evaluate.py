"""Layer 6 — running a trained policy on the real arm via LeRobot.

On real hardware the supported path is LeRobot's own control loop, which loads the
policy with its preprocessor/postprocessor pipeline and drives our registered
`LeRobotEraArm` robot. `lerobot-record --policy.path=<ckpt>` runs the policy and
records the resulting rollouts (for scoring / re-training).

`build_eval_command()` is a pure function (unit-tested); actually running it needs
the `train` extra (`uv sync --extra train`) and the physical arm.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


def build_eval_command(checkpoint: str, robot_port: str, dataset_repo_id: str,
                       num_episodes: int = 10, robot_type: str = "era_arm",
                       extra=None) -> list:
    """Return the argv for running a trained policy on the arm via `lerobot-record`."""
    cmd = [
        "lerobot-record",
        f"--robot.type={robot_type}",
        f"--robot.port={robot_port}",
        f"--policy.path={checkpoint}",
        f"--dataset.repo_id={dataset_repo_id}",
        f"--dataset.num_episodes={num_episodes}",
    ]
    if extra:
        cmd.extend(extra)
    return cmd


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run a trained era-arm policy on the arm.")
    parser.add_argument("--checkpoint", required=True, help="policy checkpoint dir or repo id")
    parser.add_argument("--port", required=True, help="serial port, e.g. /dev/era-arm")
    parser.add_argument("--dataset", required=True, help="repo_id to record the rollouts into")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="print the command, don't run it")
    parser.add_argument("extra", nargs="*", help="extra flags passed through to lerobot-record")
    args = parser.parse_args(argv)

    cmd = build_eval_command(
        checkpoint=args.checkpoint, robot_port=args.port, dataset_repo_id=args.dataset,
        num_episodes=args.episodes, extra=args.extra,
    )
    print("+ " + " ".join(cmd))
    if args.dry_run:
        return 0
    if shutil.which("lerobot-record") is None:
        print(
            "error: 'lerobot-record' not found. Install the training extra:\n"
            "    uv sync --extra train\nThen re-run (or use --dry-run here).",
            file=sys.stderr,
        )
        return 1
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
