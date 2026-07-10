"""Layer 6 — policies that turn observations into actions at eval time.

A policy answers: "given what the arm sees, what should it do next?" We keep a
`MockPolicy` for testing the rollout loop with no model, and `load_lerobot_policy`
which loads a trained LeRobot checkpoint (lazy `import` of lerobot/torch, so this
module imports fine without them).
"""

from __future__ import annotations

import numpy as np

from era_arm.driver.protocol import NUM_JOINTS


class Policy:
    """Interface: map an observation dict to a 6-angle action."""

    def reset(self) -> None:
        """Clear any temporal state between episodes. Optional."""

    def select_action(self, observation: dict):
        raise NotImplementedError


class MockPolicy(Policy):
    """A trivial test policy.

    Default: hold a fixed pose. If `follow_joints=True`, it echoes the observed
    joints back as the action (arm stays put) — handy for checking the loop wiring.
    """

    def __init__(self, pose=None, follow_joints: bool = False):
        self._pose = list(pose) if pose is not None else [0.0] * NUM_JOINTS
        self._follow = follow_joints

    def select_action(self, observation: dict):
        if self._follow:
            return np.asarray(observation["joints"], dtype=np.float32)
        return np.asarray(self._pose, dtype=np.float32)


class LeRobotPolicy(Policy):
    """Wraps a trained LeRobot policy so it fits our `select_action` interface."""

    def __init__(self, policy, device: str = "cuda"):
        self._policy = policy
        self._device = device

    def reset(self) -> None:
        if hasattr(self._policy, "reset"):
            self._policy.reset()

    def select_action(self, observation: dict):
        import torch  # lazy: only needed with a real model

        batch = {}
        for key, value in observation.items():
            if key == "watchdog":
                continue
            batch[key] = torch.as_tensor(np.asarray(value)).unsqueeze(0).to(self._device)
        with torch.no_grad():
            action = self._policy.select_action(batch)
        return action.squeeze(0).cpu().numpy().astype(np.float32)


def load_lerobot_policy(checkpoint: str, device: str = "cuda") -> LeRobotPolicy:
    """Load a trained policy from a LeRobot checkpoint dir/repo id.

    Needs the `train` extra (`uv sync --extra train`) and, for GPU inference, CUDA.
    """
    from lerobot.common.policies.factory import make_policy  # lazy import

    policy = make_policy(checkpoint)
    if hasattr(policy, "to"):
        policy = policy.to(device)
    if hasattr(policy, "eval"):
        policy.eval()
    return LeRobotPolicy(policy, device=device)
