"""Tests for services.config."""

from pathlib import Path

import pytest

from services.config import DEFAULT_MODEL, DEFAULT_PROJECTS_DIR, Config


def test_from_env_minimal_uses_defaults():
    cfg = Config.from_env({"ANTHROPIC_API_KEY": "sk-test"})
    assert cfg.anthropic_api_key == "sk-test"
    assert cfg.model == DEFAULT_MODEL
    assert cfg.projects_dir == Path(DEFAULT_PROJECTS_DIR)


def test_from_env_overrides():
    cfg = Config.from_env(
        {
            "ANTHROPIC_API_KEY": "sk-test",
            "FOUNDRY_MODEL": "claude-opus-4-8",
            "FOUNDRY_PROJECTS_DIR": "runs",
        }
    )
    assert cfg.model == "claude-opus-4-8"
    assert cfg.projects_dir == Path("runs")


def test_from_env_missing_key_does_not_raise():
    # ANTHROPIC_API_KEY is optional now (generator-only, enforced at point of use).
    cfg = Config.from_env({})
    assert cfg.anthropic_api_key == ""
    assert cfg.model == DEFAULT_MODEL


def test_from_env_blank_key_is_empty():
    cfg = Config.from_env({"ANTHROPIC_API_KEY": "   "})
    assert cfg.anthropic_api_key == ""


def test_from_env_primary_path_only_github_token():
    # System-of-record startup: only GITHUB_TOKEN, no Anthropic key.
    cfg = Config.from_env({"GITHUB_TOKEN": "ghp_x"})
    assert cfg.anthropic_api_key == ""
    assert cfg.github_token == "ghp_x"


def test_blank_overrides_fall_back_to_defaults():
    cfg = Config.from_env(
        {"ANTHROPIC_API_KEY": "sk-test", "FOUNDRY_MODEL": "  ", "FOUNDRY_PROJECTS_DIR": ""}
    )
    assert cfg.model == DEFAULT_MODEL
    assert cfg.projects_dir == Path(DEFAULT_PROJECTS_DIR)
