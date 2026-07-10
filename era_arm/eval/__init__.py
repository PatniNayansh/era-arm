"""Layer 6 — eval: run a policy on the robot and record the rollout."""

from era_arm.eval.evaluate import build_eval_command
from era_arm.eval.policy import LeRobotPolicy, MockPolicy, Policy, load_lerobot_policy
from era_arm.eval.rollout import Rollout, rollout

__all__ = [
    "Policy", "MockPolicy", "LeRobotPolicy", "load_lerobot_policy",
    "Rollout", "rollout", "build_eval_command",
]
