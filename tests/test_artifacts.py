"""Tests for services.artifacts."""

from pathlib import Path

import pytest

from services.artifacts import (
    ArtifactError,
    artifact_exists,
    artifact_path,
    list_projects,
    project_dir,
    read_artifact,
    write_artifact,
)
from services.config import Config


def _config(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def test_artifact_path_structure(tmp_path):
    cfg = _config(tmp_path)
    path = artifact_path(cfg, "foundry", "vision.md")
    assert path == cfg.projects_dir / "foundry" / "vision.md"
    assert project_dir(cfg, "foundry") == cfg.projects_dir / "foundry"


def test_write_then_read_roundtrip(tmp_path):
    cfg = _config(tmp_path)
    written = write_artifact(cfg, "foundry", "vision.md", "# Vision\n\nHello.")
    assert written.is_file()
    assert read_artifact(cfg, "foundry", "vision.md") == "# Vision\n\nHello."


def test_write_creates_project_directory(tmp_path):
    cfg = _config(tmp_path)
    assert not (cfg.projects_dir / "newproj").exists()
    write_artifact(cfg, "newproj", "product-input.md", "x")
    assert (cfg.projects_dir / "newproj").is_dir()


def test_write_overwrites(tmp_path):
    cfg = _config(tmp_path)
    write_artifact(cfg, "p", "vision.md", "first")
    write_artifact(cfg, "p", "vision.md", "second")
    assert read_artifact(cfg, "p", "vision.md") == "second"


def test_read_missing_raises(tmp_path):
    cfg = _config(tmp_path)
    with pytest.raises(ArtifactError, match="not found"):
        read_artifact(cfg, "p", "vision.md")


def test_artifact_exists(tmp_path):
    cfg = _config(tmp_path)
    assert not artifact_exists(cfg, "p", "vision.md")
    write_artifact(cfg, "p", "vision.md", "x")
    assert artifact_exists(cfg, "p", "vision.md")


def test_list_projects(tmp_path):
    cfg = _config(tmp_path)
    assert list_projects(cfg) == []
    write_artifact(cfg, "beta", "vision.md", "x")
    write_artifact(cfg, "alpha", "vision.md", "x")
    assert list_projects(cfg) == ["alpha", "beta"]


@pytest.mark.parametrize("bad", ["", "   ", ".", "..", "a/b", "a\\b", "x\x00y"])
def test_unsafe_project_name_rejected(tmp_path, bad):
    cfg = _config(tmp_path)
    with pytest.raises(ArtifactError):
        write_artifact(cfg, bad, "vision.md", "x")


@pytest.mark.parametrize("bad", ["", "..", "sub/dir.md", "../escape.md"])
def test_unsafe_artifact_name_rejected(tmp_path, bad):
    cfg = _config(tmp_path)
    with pytest.raises(ArtifactError):
        write_artifact(cfg, "p", bad, "x")
