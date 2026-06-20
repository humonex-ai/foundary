"""Foundry agents — one agent per artifact (`07-agent-catalog.md`).

Each agent reads its upstream artifact(s), fills the matching template via the
LLM, and writes exactly one artifact. Agents do not call each other; a workflow
chains them (deferred — WO-007). WO-003 adds the first: the Vision agent.
"""

from __future__ import annotations

from agents.architecture import generate_architecture
from agents.roadmap import generate_roadmap
from agents.vision import generate_vision
from agents.work_orders import generate_work_orders

__all__ = [
    "generate_vision",
    "generate_architecture",
    "generate_roadmap",
    "generate_work_orders",
]
