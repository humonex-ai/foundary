"""End-to-end loop tests (WO-008).

Exercises the whole pipeline through the chain workflow with a fake LLM, asserting
that each artifact is produced in its expected structure (the section headers its
template defines). Covers the full run, restart from every stage, partial
regeneration, and the failure paths. No network.
"""

from pathlib import Path

import pytest

from services.artifacts import ArtifactError, read_artifact, write_artifact
from services.config import Config
from services.product_input import PRODUCT_INPUT_FILENAME, ProductInputError
from services.templates import body_sections, section_headers, template_body
from workflows.chain import STAGE_NAMES, run_chain

PI_SECTIONS = [
    "Problem", "Users", "Goals", "Non-Goals", "Constraints",
    "Success Criteria", "Assumptions", "Open Questions",
]

STAGE_KEY = {
    "vision": "vision",
    "architecture": "architecture",
    "roadmap": "roadmap",
    "work-orders": "work-orders",
}
OUTPUT_FILE = {
    "vision": "00-vision.md",
    "architecture": "01-architecture.md",
    "roadmap": "02-roadmap.md",
    "work-orders": "03-work-orders.md",
}


class StructuredFakeLLM:
    """Returns the real template skeleton for each stage (selected by system-prompt
    role), so generated artifacts are structurally faithful. Records call order;
    can fail on a chosen stage."""

    _ROLE = {
        "Vision agent": "vision",
        "Architecture agent": "architecture",
        "Roadmap agent": "roadmap",
        "Work Order agent": "work-orders",
    }

    def __init__(self, fail_on: str | None = None):
        self.fail_on = fail_on
        self.calls: list[str] = []

    def complete(self, prompt: str, *, system=None, max_tokens=8192) -> str:
        stage = next(s for marker, s in self._ROLE.items() if marker in (system or ""))
        self.calls.append(stage)
        if stage == self.fail_on:
            raise RuntimeError(f"LLM failure at {stage}")
        # The template body is a structurally complete artifact skeleton.
        return template_body(STAGE_KEY[stage])


def _config(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def _product_input(project="acme") -> str:
    return f"# Product Input — {project}\n\n" + "\n\n".join(
        f"## {s}\ncontent for {s}." for s in PI_SECTIONS
    )


def _write_pi(cfg, project="acme", doc=None):
    write_artifact(cfg, project, PRODUCT_INPUT_FILENAME, doc or _product_input(project))


def _assert_structure(cfg, project, stage):
    """Each produced artifact has exactly its template's section headers."""
    content = read_artifact(cfg, project, OUTPUT_FILE[stage])
    assert section_headers(content) == body_sections(STAGE_KEY[stage])


def _exists(cfg, project, filename):
    return (cfg.projects_dir / project / filename).exists()


# --- full loop -------------------------------------------------------------

def test_full_loop_produces_all_artifacts_with_expected_structure(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = StructuredFakeLLM()

    paths = run_chain(cfg, "acme", llm=llm)

    assert llm.calls == STAGE_NAMES
    assert [p.name for p in paths] == list(OUTPUT_FILE.values())
    for stage in STAGE_NAMES:
        _assert_structure(cfg, "acme", stage)


# --- restart from every stage ---------------------------------------------

def _seed_upstream(cfg, project, up_to_stage):
    """Write placeholder upstream artifacts for stages before up_to_stage."""
    idx = STAGE_NAMES.index(up_to_stage)
    for stage in STAGE_NAMES[:idx]:
        write_artifact(cfg, project, OUTPUT_FILE[stage], f"SEED {stage}")


@pytest.mark.parametrize("entry", STAGE_NAMES)
def test_restart_from_each_stage(tmp_path, entry):
    cfg = _config(tmp_path)
    if entry == "vision":
        _write_pi(cfg)
    else:
        _seed_upstream(cfg, "acme", entry)
    llm = StructuredFakeLLM()

    run_chain(cfg, "acme", entry_stage=entry, llm=llm)

    expected_run = STAGE_NAMES[STAGE_NAMES.index(entry):]
    assert llm.calls == expected_run
    # Stages from entry forward have correct structure.
    for stage in expected_run:
        _assert_structure(cfg, "acme", stage)
    # Stages before entry were untouched (still the seed).
    for stage in STAGE_NAMES[: STAGE_NAMES.index(entry)]:
        assert read_artifact(cfg, "acme", OUTPUT_FILE[stage]) == f"SEED {stage}"


# --- partial regeneration --------------------------------------------------

def test_partial_regeneration_overwrites_only_downstream(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    run_chain(cfg, "acme", llm=StructuredFakeLLM())  # full run

    # Mutate vision + roadmap by hand, then restart from architecture.
    write_artifact(cfg, "acme", "00-vision.md", "EDITED VISION")
    write_artifact(cfg, "acme", "02-roadmap.md", "STALE ROADMAP")

    run_chain(cfg, "acme", entry_stage="architecture", llm=StructuredFakeLLM())

    # Vision (upstream of entry) preserved; roadmap (downstream) regenerated.
    assert read_artifact(cfg, "acme", "00-vision.md") == "EDITED VISION"
    _assert_structure(cfg, "acme", "roadmap")
    _assert_structure(cfg, "acme", "work-orders")


# --- failure paths ---------------------------------------------------------

def test_invalid_product_input(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg, doc="# Product Input — acme\n\n## Problem\nonly one section\n")
    llm = StructuredFakeLLM()
    with pytest.raises(ProductInputError):
        run_chain(cfg, "acme", llm=llm)
    assert llm.calls == []
    assert not _exists(cfg, "acme", "00-vision.md")


def test_missing_upstream_artifact(tmp_path):
    cfg = _config(tmp_path)  # no vision present
    llm = StructuredFakeLLM()
    with pytest.raises(ArtifactError, match="not found"):
        run_chain(cfg, "acme", entry_stage="roadmap", llm=llm)
    assert llm.calls == []


def test_llm_failure_midchain(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = StructuredFakeLLM(fail_on="architecture")
    with pytest.raises(RuntimeError, match="LLM failure at architecture"):
        run_chain(cfg, "acme", llm=llm)
    # Vision wrote; architecture failed; downstream never ran.
    assert llm.calls == ["vision", "architecture"]
    assert _exists(cfg, "acme", "00-vision.md")
    assert not _exists(cfg, "acme", "02-roadmap.md")
    assert not _exists(cfg, "acme", "03-work-orders.md")
