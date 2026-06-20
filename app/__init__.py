"""Foundry application-service layer (MCP V1).

Thin orchestration between the MCP adapter and the Foundry library. The six
services map 1:1 to the MCP V1 tools.
"""

from __future__ import annotations

from app.projects import (
    ProjectSummary,
    approve_project,
    create_project,
    list_projects,
    regenerate,
    show_project,
    sync_github,
)

__all__ = [
    "ProjectSummary",
    "list_projects",
    "create_project",
    "show_project",
    "regenerate",
    "approve_project",
    "sync_github",
]
