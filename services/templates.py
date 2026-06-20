"""Template registry and loader (WO-002).

Templates are plain markdown files in ``templates/`` (``06-decisions.md`` D-009).
Each file has two parts separated by :data:`BODY_MARKER`:

- a **guidance** block — ``## Purpose``, ``## Required Sections``, ``## How To Use``
  (for humans and agents);
- a **body** — the artifact skeleton: ``##`` sections an agent fills, always
  including ``## Assumptions``.

This module only reads templates and reports their structure. It does not render,
generate, or fill them — that is the agents' job (WO-003+), out of scope here. No
schema engine, no database.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Separates the guidance block (above) from the artifact skeleton (below).
BODY_MARKER = "<!-- TEMPLATE BODY -->"

_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


class TemplateError(RuntimeError):
    """Raised for an unknown template key or a malformed template file."""


@dataclass(frozen=True)
class Template:
    """Static metadata for one artifact template."""

    key: str
    title: str
    output_filename: str
    upstream: tuple[str, ...]  # upstream artifact filenames; empty for the chain head


# The artifact chain (`02-architecture.md`, Shape in One Line). Order matters.
TEMPLATES: dict[str, Template] = {
    "product-input": Template("product-input", "Product Input", "product-input.md", ()),
    "vision": Template("vision", "Vision", "00-vision.md", ("product-input.md",)),
    "architecture": Template(
        "architecture", "Architecture", "01-architecture.md", ("00-vision.md",)
    ),
    "roadmap": Template(
        "roadmap", "Roadmap", "02-roadmap.md", ("00-vision.md", "01-architecture.md")
    ),
    "work-orders": Template(
        "work-orders", "Work Orders", "03-work-orders.md", ("02-roadmap.md",)
    ),
}


def template_keys() -> list[str]:
    """Return the template keys in chain order."""
    return list(TEMPLATES)


def get_template(key: str) -> Template:
    """Return the :class:`Template` metadata for ``key``."""
    try:
        return TEMPLATES[key]
    except KeyError:
        raise TemplateError(
            f"Unknown template {key!r}. Known: {', '.join(TEMPLATES)}"
        ) from None


def template_path(key: str) -> Path:
    """Return the file path for a template key."""
    get_template(key)  # validate key
    return TEMPLATES_DIR / f"{key}.md"


def load_template(key: str) -> str:
    """Return the full text of a template file."""
    path = template_path(key)
    if not path.is_file():
        raise TemplateError(f"Template file missing: {path}")
    return path.read_text(encoding="utf-8")


def split_template(key: str) -> tuple[str, str]:
    """Return ``(guidance, body)`` for a template, split on :data:`BODY_MARKER`.

    Raises :class:`TemplateError` if the marker is absent.
    """
    text = load_template(key)
    if BODY_MARKER not in text:
        raise TemplateError(f"Template {key!r} is missing {BODY_MARKER!r}.")
    guidance, body = text.split(BODY_MARKER, 1)
    return guidance.strip(), body.strip()


def template_guidance(key: str) -> str:
    """Return the guidance block (Purpose / Required Sections / How To Use)."""
    return split_template(key)[0]


def template_body(key: str) -> str:
    """Return the artifact skeleton an agent fills."""
    return split_template(key)[1]


def section_headers(markdown: str) -> list[str]:
    """Return the level-2 (``##``) section titles in ``markdown``, in order."""
    return [m.strip() for m in _HEADER_RE.findall(markdown)]


def body_sections(key: str) -> list[str]:
    """Return the skeleton's ``##`` section titles for a template."""
    return section_headers(template_body(key))
