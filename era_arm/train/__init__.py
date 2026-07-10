"""Layer 5 — train: build/run LeRobot training for era-arm policies."""

from era_arm.train.train import SUPPORTED_POLICIES, build_train_command

__all__ = ["build_train_command", "SUPPORTED_POLICIES"]
