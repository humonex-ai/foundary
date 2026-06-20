"""Foundry MCP server (MCP V1) — a thin adapter over ``app/*``.

Exposes six tools. Each builds a Config from the environment and delegates to one
application service; the server holds no business logic. Local stdio transport,
single founder, no auth.

Run: ``foundry-mcp`` (console script) or ``python -m mcp_server``.
"""

from __future__ import annotations

from typing import Any

from app import projects as app
from services.config import Config


def _cfg() -> Config:
    return Config.from_env()


# --- tool implementations (each = one app call) ----------------------------

def list_projects() -> list[dict[str, str]]:
    """List all Foundry projects and their lifecycle state."""
    return [{"name": s.name, "state": s.lifecycle} for s in app.list_projects(_cfg())]


def create_project(name: str, product_input: str) -> dict[str, Any]:
    """Create a project from a complete Product Input and generate all artifacts."""
    return app.create_project(_cfg(), name, product_input)


def show_project(name: str, artifact: str | None = None) -> dict[str, Any]:
    """Show a project's lifecycle state and artifacts; optionally one artifact's content."""
    return app.show_project(_cfg(), name, artifact)


def regenerate(name: str, from_stage: str) -> dict[str, Any]:
    """Re-run the chain from a stage to the end; marks Stale if an approved plan changed."""
    return app.regenerate(_cfg(), name, from_stage)


def approve_project(name: str) -> dict[str, Any]:
    """Record founder approval of the current plan (required before sync)."""
    return app.approve_project(_cfg(), name)


def sync_github(name: str, repo: str) -> dict[str, Any]:
    """Sync Work Orders to GitHub Issues. Refused unless the plan is Approved and unchanged."""
    return app.sync_github(_cfg(), name, repo)


# Adapter surface: tool name -> callable. Single source of truth for registration.
TOOLS = {
    "list_projects": list_projects,
    "create_project": create_project,
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
