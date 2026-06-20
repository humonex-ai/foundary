"""Foundry execution layer (Execution V1).

Work Orders -> GitHub Issues, one-way and idempotent. No coding agents, no PRs,
no merge automation, no queue, no database (`06-decisions.md`; Execution V1 plan).
"""

from __future__ import annotations

from execution.parse import (
    Decision,
    ParseError,
    WorkOrder,
    parse_decisions,
    parse_work_orders,
)

__all__ = [
    "WorkOrder",
    "Decision",
    "ParseError",
    "parse_work_orders",
    "parse_decisions",
]
