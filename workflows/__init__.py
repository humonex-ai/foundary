"""Foundry workflows — orchestration of the agents (`02-architecture.md`).

WO-007 adds the chain workflow: run the four agents in order from a caller-chosen
entry stage. Plain Python; no agent framework.
"""

from __future__ import annotations

from workflows.chain import (
    DEFAULT_ENTRY_STAGE,
    STAGE_NAMES,
    STAGES,
    ChainError,
    run_chain,
)

__all__ = ["run_chain", "STAGE_NAMES", "STAGES", "DEFAULT_ENTRY_STAGE", "ChainError"]
