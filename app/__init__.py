"""Foundry application-service layer (MCP V1).

Thin orchestration between the MCP adapter and the Foundry library. The six
services map 1:1 to the MCP V1 tools.
"""

from __future__ import annotations

from app.ingest import IngestError, submit_project, validate_artifacts
from app.projects import (
    ProjectSummary,
    approve_project,
    create_project,
    export,
    get_templates,
    list_projects,
    regenerate,
    show_project,
)

__all__ = [
    "ProjectSummary",
    "list_projects",
    "create_project",
    "show_project",
    "regenerate",
    "approve_project",
    "export",
    "get_templates",
    "submit_project",
    "validate_artifacts",
    "IngestError",
]
