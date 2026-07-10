"""Tests for Layer 5 — the training command builder (no lerobot/GPU needed)."""

import pytest

from era_arm.train import build_train_command


def test_build_train_command_basic():
    cmd = build_train_command(dataset="user/ds", policy="act", output="out", steps=5, batch_size=4)
    assert cmd[0] == "lerobot-train"
    assert "--policy.type=act" in cmd
    assert "--dataset.repo_id=user/ds" in cmd
    assert "--output_dir=out" in cmd
    assert "--steps=5" in cmd
    assert "--batch_size=4" in cmd


def test_build_train_command_passes_extra_flags():
    cmd = build_train_command(dataset="user/ds", extra=["--policy.chunk_size=50"])
    assert cmd[-1] == "--policy.chunk_size=50"


def test_build_train_command_rejects_unknown_policy():
    with pytest.raises(ValueError):
        build_train_command(dataset="user/ds", policy="not-a-policy")
