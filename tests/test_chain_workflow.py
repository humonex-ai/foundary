"""Tests for the chain workflow (WO-007). No network — a fake LLM is injected."""

from pathlib import Path

import pytest

from services.artifacts import ArtifactError, read_artifact, write_artifact
from services.config import Config
from services.product_input import PRODUCT_INPUT_FILENAME, ProductInputError
from workflows.chain import STAGE_NAMES, ChainError, run_chain

PI_SECTIONS = [
    "Problem", "Users", "Goals", "Non-Goals", "Constraints",
    "Success Criteria", "Assumptions", "Open Questions",
]

# Canned per-stage outputs, selected by the agent's system prompt role.
STAGE_OUTPUT = {
    "vision": "# Vision — acme\n\n## Problem\nx\n",
    "architecture": "# Architecture — acme\n\n## Overview\nx\n",
    "roadmap": "# Roadmap — acme\n\n## Goal\nx\n",
    "work-orders": "# Work Orders — acme\n\n## Format\nx\n",
}
OUTPUT_FILE = {
    "vision": "00-vision.md",
    "architecture": "01-architecture.md",
    "roadmap": "02-roadmap.md",
    "work-orders": "03-work-orders.md",
}


class FakeLLM:
    """Returns canned output per stage (detected from the system prompt role),
    records the order of stages called, and can fail on a chosen stage."""

    _ROLE = {
        "Vision agent": "vision",
        "Architecture agent": "architecture",
        "Roadmap agent": "roadmap",
        "Work Order agent": "work-orders",
    }

    def __init__(self, fail_on: str | None = None):
        self.fail_on = fail_on
        self.calls: list[str] = []

    def _stage(self, system: str) -> str:
        for marker, stage in self._ROLE.items():
            if marker in system:
                return stage
        raise AssertionError("unrecognized system prompt")

    def complete(self, prompt: str, *, system=None, max_tokens=8192) -> str:
        stage = self._stage(system or "")
        self.calls.append(stage)
        if stage == self.fail_on:
            raise RuntimeError(f"boom at {stage}")
        return STAGE_OUTPUT[stage]


def _config(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def _product_input(project="acme") -> str:
    body = f"# Product Input — {project}\n\n"
    return body + "\n\n".join(f"## {s}\ncontent for {s}." for s in PI_SECTIONS)


def _write_pi(cfg, project="acme", doc=None):
    write_artifact(cfg, project, PRODUCT_INPUT_FILENAME, doc or _product_input(project))


def _exists(cfg, project, filename):
    return (cfg.projects_dir / project / filename).exists()


# --- stage table ----------------------------------------------------------

def test_stage_names_in_order():
    assert STAGE_NAMES == ["vision", "architecture", "roadmap", "work-orders"]


# --- full chain ------------------------------------------------------------

def test_full_chain_from_product_input(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = FakeLLM()

    paths = run_chain(cfg, "acme", llm=llm)  # default entry = vision

    assert llm.calls == ["vision", "architecture", "roadmap", "work-orders"]
    assert [p.name for p in paths] == list(OUTPUT_FILE.values())
    for stage, filename in OUTPUT_FILE.items():
        assert read_artifact(cfg, "acme", filename) == STAGE_OUTPUT[stage]


def test_default_entry_is_vision(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = FakeLLM()
    run_chain(cfg, "acme", llm=llm)
    assert llm.calls[0] == "vision"


# --- stage restart ---------------------------------------------------------

def test_restart_from_architecture_skips_vision(tmp_path):
    cfg = _config(tmp_path)
    write_artifact(cfg, "acme", "00-vision.md", "SENTINEL VISION")
    llm = FakeLLM()

    paths = run_chain(cfg, "acme", entry_stage="architecture", llm=llm)

    assert llm.calls == ["architecture", "roadmap", "work-orders"]
    assert [p.name for p in paths] == ["01-architecture.md", "02-roadmap.md", "03-work-orders.md"]
    # Vision was not touched.
    assert read_artifact(cfg, "acme", "00-vision.md") == "SENTINEL VISION"


def test_restart_from_roadmap(tmp_path):
    cfg = _config(tmp_path)
    write_artifact(cfg, "acme", "00-vision.md", "V")
    write_artifact(cfg, "acme", "01-architecture.md", "A")
    llm = FakeLLM()

    run_chain(cfg, "acme", entry_stage="roadmap", llm=llm)

    assert llm.calls == ["roadmap", "work-orders"]
    assert read_artifact(cfg, "acme", "00-vision.md") == "V"
    assert read_artifact(cfg, "acme", "01-architecture.md") == "A"


def test_restart_from_work_orders_runs_only_last(tmp_path):
    cfg = _config(tmp_path)
    for f, c in [("00-vision.md", "V"), ("01-architecture.md", "A"), ("02-roadmap.md", "R")]:
        write_artifact(cfg, "acme", f, c)
    llm = FakeLLM()

    run_chain(cfg, "acme", entry_stage="work-orders", llm=llm)

    assert llm.calls == ["work-orders"]
    assert _exists(cfg, "acme", "03-work-orders.md")


def test_restart_overwrites_downstream(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = FakeLLM()
    run_chain(cfg, "acme", llm=llm)  # full run
    # Corrupt downstream, then restart from architecture.
    write_artifact(cfg, "acme", "02-roadmap.md", "STALE")
    run_chain(cfg, "acme", entry_stage="architecture", llm=FakeLLM())
    assert read_artifact(cfg, "acme", "02-roadmap.md") == STAGE_OUTPUT["roadmap"]


# --- failure paths ---------------------------------------------------------

def test_invalid_entry_stage_raises_before_running(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = FakeLLM()
    with pytest.raises(ChainError, match="Unknown entry stage"):
        run_chain(cfg, "acme", entry_stage="nope", llm=llm)
    assert llm.calls == []
    assert not _exists(cfg, "acme", "00-vision.md")


def test_missing_product_input_fails_fast(tmp_path):
    cfg = _config(tmp_path)  # no product input written
    llm = FakeLLM()
    with pytest.raises(ArtifactError, match="not found"):
        run_chain(cfg, "acme", llm=llm)
    assert llm.calls == []
    assert not _exists(cfg, "acme", "00-vision.md")


def test_invalid_product_input_fails_fast(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg, doc="# Product Input — acme\n\n## Problem\nx\n")  # missing sections
    llm = FakeLLM()
    with pytest.raises(ProductInputError):
        run_chain(cfg, "acme", llm=llm)
    assert llm.calls == []
    assert not _exists(cfg, "acme", "00-vision.md")


def test_missing_upstream_on_restart_fails_fast(tmp_path):
    cfg = _config(tmp_path)  # no 00-vision.md present
    llm = FakeLLM()
    with pytest.raises(ArtifactError, match="not found"):
        run_chain(cfg, "acme", entry_stage="architecture", llm=llm)
    assert llm.calls == []
    assert not _exists(cfg, "acme", "01-architecture.md")


def test_midchain_failure_stops_and_leaves_later_stages_unrun(tmp_path):
    cfg = _config(tmp_path)
    _write_pi(cfg)
    llm = FakeLLM(fail_on="roadmap")

    with pytest.raises(RuntimeError, match="boom at roadmap"):
        run_chain(cfg, "acme", llm=llm)

    # vision + architecture ran and wrote; roadmap attempted and failed; work-orders never ran.
    assert llm.calls == ["vision", "architecture", "roadmap"]
    assert _exists(cfg, "acme", "00-vision.md")
    assert _exists(cfg, "acme", "01-architecture.md")
    assert not _exists(cfg, "acme", "03-work-orders.md")
