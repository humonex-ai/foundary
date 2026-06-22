"""Foundry MCP server (MCP V1) — a thin adapter over ``app/*``.

Exposes six tools. Each builds a Config from the environment and delegates to one
application service; the server holds no business logic. Local stdio transport,
single founder, no auth.

Run: ``foundry-mcp`` (console script) or ``python -m mcp_server``.
"""

from __future__ import annotations

from typing import Any

from app import ingest as ingest_app
from app import projects as app
from services.config import Config


def _cfg() -> Config:
    return Config.from_env()


# --- tool implementations (each = one app call) ----------------------------

def list_projects() -> list[dict[str, str]]:
    """List all Foundry projects and their lifecycle state."""
    return [{"name": s.name, "state": s.lifecycle} for s in app.list_projects(_cfg())]


def create_project(name: str, product_input: str) -> dict[str, Any]:
    """[LEGACY GENERATOR] Generate all artifacts internally from a Product Input
    via the LLM. Prefer `submit_project` (the primary, system-of-record path).
    This path is compatibility-only and pending retirement; it requires
    ANTHROPIC_API_KEY."""
    return app.create_project(_cfg(), name, product_input)


def get_templates(artifact: str | None = None) -> dict[str, str]:
    """Return the canonical artifact templates. CALL THIS BEFORE authoring
    artifacts for submit_project — it gives the exact required sections, the
    Decision List pipe-table format, and the per-Work-Order fields (incl.
    `Depends on:` and `D-NNN` decision ids). Omit `artifact` for all five."""
    return app.get_templates(artifact)


def submit_project(name: str, artifacts: dict[str, str]) -> dict[str, Any]:
    """[PRIMARY] Store client-authored artifacts (vision/architecture/roadmap/
    work-orders, optional product-input) as a project after structural + reference
    validation. Author artifacts from get_templates first. Your chat authors them,
    Foundry validates, records, gates, and exports. No internal LLM — needs no
    ANTHROPIC_API_KEY."""
    return ingest_app.submit_project(_cfg(), name, artifacts)


def show_project(name: str, artifact: str | None = None) -> dict[str, Any]:
    """Show a project's lifecycle state and artifacts; optionally one artifact's content."""
    return app.show_project(_cfg(), name, artifact)


def regenerate(name: str, from_stage: str) -> dict[str, Any]:
    """[LEGACY GENERATOR] Re-run the LLM chain from a stage to the end. Obsolete
    under the system-of-record path — regenerate in your chat and re-submit via
    `submit_project` instead. Requires ANTHROPIC_API_KEY."""
    return app.regenerate(_cfg(), name, from_stage)


def approve_project(name: str) -> dict[str, Any]:
    """Record founder approval of the current plan (required before sync)."""
    return app.approve_project(_cfg(), name)


def sync_github(name: str, repo: str) -> dict[str, Any]:
    """Export Work Orders to GitHub Issues. Refused unless the plan is Approved and
    unchanged. Delegates to the single shared export path."""
    return app.export(_cfg(), name, repo, via="mcp")


# Adapter surface: tool name -> callable. Single source of truth for registration.
TOOLS = {
    "list_projects": list_projects,
    "get_templates": get_templates,
    "create_project": create_project,
    "submit_project": submit_project,
    "show_project": show_project,
    "regenerate": regenerate,
    "approve_project": approve_project,
    "sync_github": sync_github,
}


def build_server():
    """Build the FastMCP server with the six tools registered."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("foundry")
    for fn in TOOLS.values():
        server.tool()(fn)
    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
