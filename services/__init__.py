"""Foundry services — the thin shared layer the agents depend on (WO-001).

Three capabilities only (``02-architecture.md``, ``services/``):
- configuration loading (:mod:`services.config`)
- the LLM client (:mod:`services.llm`)
- artifact file I/O (:mod:`services.artifacts`)

Nothing agent-specific and no orchestration lives here.
"""

from __future__ import annotations

from services.artifacts import (
    ArtifactError,
    artifact_exists,
    artifact_path,
    list_projects,
    project_dir,
    read_artifact,
    write_artifact,
)
from services.config import Config, ConfigError
from services.llm import LLMClient, LLMError
from services.product_input import (
    PRODUCT_INPUT_FILENAME,
    REQUIRED_SECTIONS,
    ProductInputError,
    load_and_validate,
    load_product_input,
    missing_sections,
    validate_product_input,
)
from services.templates import (
    TEMPLATES,
    Template,
    TemplateError,
    body_sections,
    get_template,
    load_template,
    section_headers,
    split_template,
    template_body,
    template_guidance,
    template_keys,
    template_path,
)

__all__ = [
    "Config",
    "ConfigError",
    "LLMClient",
    "LLMError",
    "ArtifactError",
    "artifact_path",
    "project_dir",
    "write_artifact",
    "read_artifact",
    "artifact_exists",
    "list_projects",
    "TEMPLATES",
    "Template",
    "TemplateError",
    "template_keys",
    "get_template",
    "template_path",
    "load_template",
    "split_template",
    "template_guidance",
    "template_body",
    "section_headers",
    "body_sections",
    "PRODUCT_INPUT_FILENAME",
    "REQUIRED_SECTIONS",
    "ProductInputError",
    "missing_sections",
    "validate_product_input",
    "load_product_input",
    "load_and_validate",
]
