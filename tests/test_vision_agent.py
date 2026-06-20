"""Tests for the Vision agent (WO-003). No network — a fake LLM is injected."""

from pathlib import Path

import pytest

from agents.vision import build_prompt, generate_vision
from services.artifacts import ArtifactError, read_artifact, write_artifact
from services.config import Config
from services.product_input import PRODUCT_INPUT_FILENAME, ProductInputError

PI_SECTIONS = [
    "Problem", "Users", "Goals", "Non-Goals", "Constraints",
    "Success Criteria", "Assumptions", "Open Questions",
]

VISION_OUTPUT = """\
# Vision — acme

## Problem
Agents waste time.

## Users
Support agents.

## Goals
Faster tickets.

## Non-Goals
Not a CRM.

## Success Criteria
Handle time < 3 min.

## Assumptions
Shopify in use.
"""


class FakeLLM:
    """Captures the prompt/system and returns a canned response."""

    def __init__(self, response: str):
        self._response = response
        self.prompt = None
        self.system = None
        self.calls = 0

    def complete(self, prompt: str, *, system=None, max_tokens=8192) -> str:
        self.prompt = prompt
        self.system = system
        self.calls += 1
        return self._response


def _product_input(project="acme") -> str:
    body = f"# Product Input — {project}\n\n"
    body += "\n\n".join(f"## {s}\ncontent for {s}." for s in PI_SECTIONS)
    return body


def _config(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def _write_pi(cfg, project="acme", doc=None):
    write_artifact(cfg, project, PRODUCT_INPUT_FILENAME, doc or _product_input(project))


def test_generates_and_writes_vision(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = FakeLLM(VISION_OUTPUT)

    path = generate_vision(cfg, "acme", llm=llm)

    assert path == cfg.projects_dir / "acme" / "00-vision.md"
    assert path.is_file()
    assert read_artifact(cfg, "acme", "00-vision.md") == VISION_OUTPUT
    assert llm.calls == 1


def test_prompt_includes_product_input_and_template(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = FakeLLM(VISION_OUTPUT)

    generate_vision(cfg, "acme", llm=llm)

    # Product Input content reached the model.
    assert "content for Problem." in llm.prompt
    # Template skeleton headers reached the model.
    assert "## Assumptions" in llm.prompt
    # System prompt establishes the vision-only boundary.
    assert "Vision agent" in llm.system
    assert "Do NOT propose architecture" in llm.system
    # Refinement: preserve Constraints; build the Decision List.
    assert "Constraints" in llm.system
    assert "Decision List" in llm.system
    # Template skeleton now carries Constraints + Decision List sections.
    assert "## Constraints" in llm.prompt
    assert "## Decision List" in llm.prompt


def test_build_prompt_substitutes_project():
    prompt = build_prompt(_product_input("zeta"), "zeta")
    assert "{{ project }}" not in prompt
    assert "# Vision — zeta" in prompt


def test_missing_product_input_fails_clearly(tmp_path):
    cfg = _config(tmp_path)
    llm = FakeLLM(VISION_OUTPUT)
    with pytest.raises(ArtifactError, match="not found"):
        generate_vision(cfg, "acme", llm=llm)
    assert llm.calls == 0  # never called the LLM
    assert not (cfg.projects_dir / "acme" / "00-vision.md").exists()


def test_invalid_product_input_fails_clearly(tmp_path):
    cfg = _config(tmp_path)
    incomplete = "# Product Input — acme\n\n## Problem\nx\n\n## Users\ny\n"
    _write_pi(cfg, doc=incomplete)
    llm = FakeLLM(VISION_OUTPUT)

    with pytest.raises(ProductInputError):
        generate_vision(cfg, "acme", llm=llm)
    assert llm.calls == 0
    assert not (cfg.projects_dir / "acme" / "00-vision.md").exists()
