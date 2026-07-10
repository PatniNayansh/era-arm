"""Layer 4 — the Teleoperator interface.

A teleoperator is any source of *actions* for the arm during data collection:
a human moving a leader arm, pressing keys, or a scripted trajectory for testing.
They all answer one question each control tick: "what should the arm do now?"
"""

from __future__ import annotations


class Teleoperator:
    """Base class / interface for anything that produces actions."""

    def start(self) -> None:
        """Begin producing actions (open devices, reset state). Optional."""

    def get_action(self) -> dict:
        """Return the next action as a flat LeRobot dict: {"<joint>.pos": angle, ...}."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop producing actions (close devices). Optional."""
