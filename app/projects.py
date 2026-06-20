"""Application services for MCP V1 (thin orchestration over the Foundry library).

Each function composes existing services/agents/workflow/execution code plus the
project-state service. The MCP server calls only these; it holds no logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app import state as state_mod
from execution import sync as exec_sync
from execution.parse import parse_decisions, parse_work_orders
from services import artifacts, product_input
from services.config import Config
from services.llm import LLMClient
from services.templates import TEMPLATES, get_template
from workflows.chain import STAGE_NAMES, run_chain

# Artifact keys the founder can read via show_project.
_ARTIFACT_KEYS = {
    "product-input": product_input.PRODUCT_INPUT_FILENAME,
    **{k: t.output_filename for k, t in TEMPLATES.items()},
}


@dataclass
class ProjectSummary:
    name: str
    lifecycle: str


def list_projects(config: Config) -> list[ProjectSummary]:
    """All projects under the projects root, with their lifecycle state."""
    return [
        ProjectSummary(name=n, lifecycle=state_mod.load_state(config, n).lifecycle)
        for n in artifacts.list_projects(config)
    ]


def create_project(
    config: Config, name: str, product_input_md: str, *, llm: LLMClient | None = None
) -> dict:
    """Create a project from a complete Product Input and generate all artifacts.

    Writes ``product-input.md``, validates it (fails clearly on missing
    sections), runs the full chain, and marks the project Draft. The Product
    Input must be authored upstream (by the chat) — this does not write it from a
    transcript.
    """
    artifacts.write_artifact(
        config, name, product_input.PRODUCT_INPUT_FILENAME, product_input_md
    )
    # Fail fast on an incomplete Product Input — before any LLM call.
    product_input.validate_product_input(product_input_md)

    paths = run_chain(config, name, entry_stage="vision", llm=llm)
    st = state_mod.mark_draft(config, name)
    return {
        "name": name,
        "state": st.lifecycle,
        "artifacts": [p.name for p in paths],
    }


def show_project(config: Config, name: str, artifact: str | None = None) -> dict:
    """Read-only view: lifecycle + which artifacts exist; optionally one's content."""
    st = state_mod.load_state(config, name)
    present = {
        key: artifacts.artifact_exists(config, name, fname)
        for key, fname in _ARTIFACT_KEYS.items()
    }
    result: dict = {"name": name, "state": st.lifecycle, "artifacts": present}
    if artifact is not None:
        if artifact not in _ARTIFACT_KEYS:
            raise ValueError(
                f"Unknown artifact {artifact!r}. Known: {', '.join(_ARTIFACT_KEYS)}"
            )
        result["content"] = artifacts.read_artifact(config, name, _ARTIFACT_KEYS[artifact])
    return result


def regenerate(
    config: Config, name: str, from_stage: str, *, llm: LLMClient | None = None
) -> dict:
    """Re-run the chain from ``from_stage`` to the end; flip to Stale if the plan
    changed after approval."""
    if from_stage not in STAGE_NAMES:
        raise ValueError(
            f"Unknown stage {from_stage!r}. Valid: {', '.join(STAGE_NAMES)}"
        )
    paths = run_chain(config, name, entry_stage=from_stage, llm=llm)
    st = state_mod.stale_if_changed(config, name)
    return {
        "name": name,
        "regenerated": [p.name for p in paths],
        "state": st.lifecycle,
    }


def approve_project(config: Config, name: str) -> dict:
    """Record founder approval of the current plan (gate for sync)."""
    st = state_mod.approve(config, name)
    return {
        "name": name,
        "state": st.lifecycle,
        "plan_fingerprint": st.approved_fingerprint,
        "approved_at": st.approvals[-1]["at"] if st.approvals else None,
    }


def sync_github(config: Config, name: str, repo: str, *, gh=None) -> dict:
    """Guarded GitHub issue sync: only an Approved, unchanged plan may sync."""
    allowed, reason = state_mod.sync_allowed(config, name)
    if not allowed:
        return {"name": name, "synced": False, "refused_reason": reason,
                "state": state_mod.load_state(config, name).lifecycle}

    md = artifacts.read_artifact(config, name, get_template("work-orders").output_filename)
    work_orders = parse_work_orders(md)
    decisions = parse_decisions(md)
    client = gh if gh is not None else _github_client(config)
    report = exec_sync.sync(name, repo, work_orders, decisions, client)
    st = state_mod.mark_synced(config, name)
    counts: dict[str, int] = {}
    for a in report.actions:
        counts[a.action] = counts.get(a.action, 0) + 1
    return {"name": name, "synced": True, "state": st.lifecycle, "summary": counts}


def _github_client(config: Config):
    from services.github import GitHubClient

    return GitHubClient(config.github_token)
