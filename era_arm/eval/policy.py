"""Layer 6 — policies that turn observations into actions at eval time.

A policy maps a flat LeRobot observation dict ("<joint>.pos" + camera-name keys) to
a flat action dict ("<joint>.pos"). `MockPolicy` tests the loop with no model.
`load_lerobot_policy` loads a trained checkpoint via LeRobot's real loader
(`PreTrainedPolicy.from_pretrained`).

IMPORTANT: the fully-supported way to run a trained policy on the real arm is
LeRobot's own CLI — `lerobot-record --policy.path=<ckpt>` (or `lerobot-eval` in sim)
— which runs the complete preprocessor -> policy -> postprocessor pipeline against
`LeRobotEraArm`. See era_arm/eval/evaluate.py and the README. `LeRobotPolicy` below
is a convenience adapter for programmatic use and should be validated against your
installed LeRobot version before trusting it on hardware.
"""

from __future__ import annotations

import numpy as np

from era_arm.driver.protocol import NUM_JOINTS
from era_arm.robot import MOTOR_KEYS, action_from_targets


class Policy:
    """Interface: map an observation dict to a flat "<joint>.pos" action dict."""

    def reset(self) -> None:
        """Clear any temporal state between episodes. Optional."""

    def select_action(self, observation: dict) -> dict:
        raise NotImplementedError


class MockPolicy(Policy):
    """A trivial test policy.

    Default: command a fixed pose. If `follow_joints=True`, echo the observed joint
    positions back (arm holds still) — handy for verifying the loop wiring.
    """

    def __init__(self, pose=None, follow_joints: bool = False):
        self._pose = list(pose) if pose is not None else [0.0] * NUM_JOINTS
        self._follow = follow_joints

    def select_action(self, observation: dict) -> dict:
        if self._follow:
            targets = [float(observation[key]) for key in MOTOR_KEYS]
        else:
            targets = self._pose
        return action_from_targets(targets)


class LeRobotPolicy(Policy):
    """Adapter around a trained LeRobot policy (see module note; prefer the CLI)."""

    def __init__(self, policy, device: str = "cuda"):
        self._policy = policy
        self._device = device

    def reset(self) -> None:
        if hasattr(self._policy, "reset"):
            self._policy.reset()

    def select_action(self, observation: dict) -> dict:
        import torch  # lazy: only needed with a real model

        # Build the batch with the LeRobot dataset keys the policy was trained on.
        state = torch.tensor(
            [[float(observation[key]) for key in MOTOR_KEYS]], dtype=torch.float32
        )
        batch = {"observation.state": state.to(self._device)}
        for key, value in observation.items():
            if key in MOTOR_KEYS:
                continue  # a camera frame
            img = torch.as_tensor(np.asarray(value))
            if img.ndim == 3:  # HxWxC uint8 -> 1xCxHxW float in [0, 1]
                img = img.permute(2, 0, 1).to(torch.float32) / 255.0
                img = img.unsqueeze(0)
            batch[f"observation.images.{key}"] = img.to(self._device)

        with torch.no_grad():
            action = self._policy.select_action(batch)
        targets = action.squeeze(0).cpu().numpy().tolist()
        return action_from_targets(targets)


def load_lerobot_policy(checkpoint: str, device: str = "cuda") -> LeRobotPolicy:
    """Load a trained policy from a LeRobot checkpoint dir/repo id via from_pretrained.

    Needs the `train` extra (`uv sync --extra train`) and, for GPU inference, CUDA.
    """
    from lerobot.configs.policies import PreTrainedConfig  # lazy imports
    from lerobot.policies.factory import get_policy_class

    cfg = PreTrainedConfig.from_pretrained(checkpoint)
    policy = get_policy_class(cfg.type).from_pretrained(checkpoint)
    if hasattr(policy, "to"):
        policy = policy.to(device)
    if hasattr(policy, "eval"):
        policy.eval()
    return LeRobotPolicy(policy, device=device)
