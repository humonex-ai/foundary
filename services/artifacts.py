"""Artifact file I/O.

Generated artifacts are plain markdown files on disk (``06-decisions.md`` D-004),
one directory per project under the configured projects root
(``02-architecture.md``, Output Location; D-008):

    projects/<name>/product-input.md
    projects/<name>/vision.md
    projects/<name>/architecture.md
    projects/<name>/roadmap.md
    projects/<name>/work-orders.md

This module owns *only* reading and writing those files. It does not know what an
artifact means — that is the agents' job (out of scope for WO-001).
"""

from __future__ import annotations

from pathlib import Path

from services.config import Config


class ArtifactError(RuntimeError):
    """Raised when an artifact path or name is invalid, or a read target is missing."""


def _safe_segment(value: str, label: str) -> str:
    """Validate a single path segment (project name or artifact filename).

    Rejects empty values and anything that could escape the projects root —
    separators and parent references. Keeps writes confined to
    ``projects/<name>/`` (D-008).
    """
    cleaned = value.strip()
    if not cleaned:
        raise ArtifactError(f"{label} must not be empty.")
    if cleaned in {".", ".."} or "/" in cleaned or "\\" in cleaned or "\x00" in cleaned:
        raise ArtifactError(f"{label} {value!r} is not a valid path segment.")
    return cleaned


def project_dir(config: Config, project: str) -> Path:
    """Return the directory for a project's artifacts: ``<projects_dir>/<project>``."""
    name = _safe_segment(project, "project name")
    return config.projects_dir / name


def artifact_path(config: Config, project: str, name: str) -> Path:
    """Return the full path to one artifact file within a project."""
    filename = _safe_segment(name, "artifact name")
    return project_dir(config, project) / filename


def write_artifact(config: Config, project: str, name: str, content: str) -> Path:
    """Write ``content`` to ``projects/<project>/<name>``, creating the directory.

    Returns the path written. Overwrites any existing file (V1 has no versioning;
    D-004).
    """
    path = artifact_path(config, project, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def read_artifact(config: Config, project: str, name: str) -> str:
    """Read and return the text of ``projects/<project>/<name>``.

    Raises :class:`ArtifactError` if the file does not exist.
    """
    path = artifact_path(config, project, name)
    if not path.is_file():
        raise ArtifactError(f"Artifact not found: {path}")
    return path.read_text(encoding="utf-8")


def artifact_exists(config: Config, project: str, name: str) -> bool:
    """Return whether ``projects/<project>/<name>`` exists as a file."""
    return artifact_path(config, project, name).is_file()


def list_projects(config: Config) -> list[str]:
    """Return the names of projects that have a directory under the projects root.

    Returns an empty list if the projects root does not exist yet.
    """
    root = config.projects_dir
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())
