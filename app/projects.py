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
from services.templates import (
    TEMPLATES,
    TemplateError,
    get_template,
    load_template,
    template_keys,
)
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


def get_templates(artifact: str | None = None) -> dict[str, str]:
    """Return the canonical artifact templates so a client authors the exact
    shape ``submit_project`` expects — required sections, the Decision List
    pipe-table, and the per-Work-Order fields (incl. ``Depends on:``).

    ``artifact`` selects one key (product-input/vision/architecture/roadmap/
    work-orders); omit it for all. Read these before authoring artifacts.
    """
    keys = template_keys() if artifact is None else [artifact]
    out: dict[str, str] = {}
    for key in keys:
        try:
            out[key] = load_template(key)
        except TemplateError as exc:
            raise ValueError(str(exc)) from None
    return out


def list_projects(config: Config) -> list[ProjectSummary]:
    """All projects under the projects root, with their lifecycle state."""
    return [
        ProjectSummary(name=n, lifecycle=state_mod.load_state(config, n).lifecycle)
        for n in artifacts.list_projects(config)
    ]


def create_project(
    config: Config, name: str, product_input_md: str, *, llm: LLMClient | None = None
) -> dict:
    """[LEGACY / COMPATIBILITY] Generate all artifacts internally via the LLM.

    Superseded by the system-of-record path (`app.ingest.submit_project`); kept for
    compatibility, pending retirement (`06-decisions.md` D-013). Requires an
    Anthropic key.

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
    """[LEGACY / COMPATIBILITY] Re-run the LLM chain from ``from_stage`` to the end;
    flip to Stale if the plan changed after approval.

    Obsolete under the system-of-record path — regenerate in the client and
    re-submit via `app.ingest.submit_project` (`06-decisions.md` D-013)."""
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


def export(
    config: Config,
    name: str,
    repo: str,
    *,
    gh=None,
    dry_run: bool = False,
    reconcile: bool = False,
    via: str = "mcp",
) -> dict:
    """The single guarded export path (M1). Both the MCP `sync_github` tool and
    the CLI `sync-issues` command delegate here; nothing else calls
    ``execution.sync.sync``.

    Enforces the export guard (Approved + current fingerprint == approved), runs
    the GitHub issue sync (honoring ``dry_run`` and ``reconcile``), and — only on
    a successful real (non-dry-run) sync — records an export event. Lifecycle is
    not changed by export.
    """
    allowed, reason = state_mod.export_allowed(config, name)
    if not allowed:
        return {"name": name, "synced": False, "dry_run": dry_run,
                "refused_reason": reason,
                "state": state_mod.load_state(config, name).lifecycle}

    md = artifacts.read_artifact(config, name, get_template("work-orders").output_filename)
    work_orders = parse_work_orders(md)
    decisions = parse_decisions(md)
    client = gh if gh is not None else _github_client(config)
    report = exec_sync.sync(name, repo, work_orders, decisions, client,
                            dry_run=dry_run, reconcile=reconcile)

    if not dry_run:
        state_mod.record_export(
            config, name, target="github", ref=repo,
            fingerprint=state_mod.plan_fingerprint(config, name), via=via,
        )

    counts: dict[str, int] = {}
    for a in report.actions:
        counts[a.action] = counts.get(a.action, 0) + 1
    return {
        "name": name,
        "synced": not dry_run,
        "dry_run": dry_run,
        "state": state_mod.load_state(config, name).lifecycle,
        "summary": counts,
        "actions": [{"action": a.action, "wo_id": a.wo_id, "number": a.number,
                     "note": a.note} for a in report.actions],
    }


def _github_client(config: Config):
    from services.github import GitHubClient

    return GitHubClient(config.github_token)
