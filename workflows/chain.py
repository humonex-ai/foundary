"""Chain workflow (WO-007).

Orchestrates the existing agents into the core loop:

    Product Input -> Vision -> Architecture -> Roadmap -> Work Orders

It is plain Python — a list of stages and a loop (`06-decisions.md` D-010); no
agent framework, no CLI, no service. The workflow reuses the agents exactly as
implemented: it changes no prompt, template, or agent logic. Each agent reads its
upstream artifact(s) from disk and overwrites its own output, so running from a
chosen entry stage forward regenerates that artifact and every downstream one
(the V1 coherence mechanism, `02-architecture.md`).

The entry stage is chosen by the caller. There is no automatic drift detection
and no stage inference: the caller says where to start, the workflow runs from
there to the end. Validation is whatever each agent already enforces — Product
Input structural validation before Vision, upstream-file presence for the rest —
and failures propagate immediately (fail fast).
"""

from __future__ import annotations

from pathlib import Path

from agents.architecture import generate_architecture
from agents.roadmap import generate_roadmap
from agents.vision import generate_vision
from agents.work_orders import generate_work_orders
from services.config import Config
from services.llm import LLMClient

# The runnable stages, in chain order. Each is (name, agent function). The agent
# functions are reused unchanged; the workflow only sequences them.
STAGES: list[tuple[str, object]] = [
    ("vision", generate_vision),
    ("architecture", generate_architecture),
    ("roadmap", generate_roadmap),
    ("work-orders", generate_work_orders),
]

STAGE_NAMES: list[str] = [name for name, _ in STAGES]

DEFAULT_ENTRY_STAGE = "vision"


class ChainError(RuntimeError):
    """Raised for an invalid entry stage. (Agent/validation errors propagate as-is.)"""


def _entry_index(entry_stage: str) -> int:
    try:
        return STAGE_NAMES.index(entry_stage)
    except ValueError:
        raise ChainError(
            f"Unknown entry stage {entry_stage!r}. Valid stages, in order: "
            + ", ".join(STAGE_NAMES)
            + "."
        ) from None


def run_chain(
    config: Config,
    project: str,
    *,
    entry_stage: str = DEFAULT_ENTRY_STAGE,
    llm: LLMClient | None = None,
) -> list[Path]:
    """Run the pipeline from ``entry_stage`` to the end and return paths written.

    Stages run in order starting at ``entry_stage`` (default ``"vision"`` — the
    full chain). Each stage reads its upstream artifact(s) from
    ``projects/<project>/`` and overwrites its own output; downstream artifacts
    are thereby regenerated. The caller chooses the entry stage; the workflow does
    not infer it or detect drift.

    ``llm`` is injectable and passed to every agent (tests supply a fake); when
    omitted each agent constructs a real :class:`LLMClient` from ``config``.

    Raises :class:`ChainError` for an invalid entry stage (before running
    anything). Any validation or upstream error raised by an agent — e.g.
    :class:`services.product_input.ProductInputError` or
    :class:`services.artifacts.ArtifactError` — propagates immediately, stopping
    the chain (fail fast); stages after the failure do not run.
    """
    start = _entry_index(entry_stage)

    written: list[Path] = []
    for _name, generate in STAGES[start:]:
        path = generate(config, project, llm=llm)
        written.append(path)
    return written
