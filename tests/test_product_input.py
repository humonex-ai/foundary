"""Tests for services.product_input (WO-002b)."""

from pathlib import Path

import pytest

from services.artifacts import ArtifactError, write_artifact
from services.config import Config
from services.product_input import (
    PRODUCT_INPUT_FILENAME,
    REQUIRED_SECTIONS,
    ProductInputError,
    load_and_validate,
    load_product_input,
    missing_sections,
    validate_product_input,
)

ALL_SECTIONS = [
    "Problem", "Users", "Goals", "Non-Goals", "Constraints",
    "Success Criteria", "Assumptions", "Open Questions",
]


def _doc(sections) -> str:
    body = "# Product Input — test\n\n"
    body += "\n\n".join(f"## {s}\ncontent for {s}." for s in sections)
    return body


def _config(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def test_required_sections_match_template():
    assert list(REQUIRED_SECTIONS) == ALL_SECTIONS


def test_filename_is_product_input_md():
    assert PRODUCT_INPUT_FILENAME == "product-input.md"


def test_complete_document_validates():
    validate_product_input(_doc(ALL_SECTIONS))  # no raise
    assert missing_sections(_doc(ALL_SECTIONS)) == []


def test_missing_one_section_reported():
    doc = _doc([s for s in ALL_SECTIONS if s != "Non-Goals"])
    assert missing_sections(doc) == ["Non-Goals"]
    with pytest.raises(ProductInputError, match="Non-Goals"):
        validate_product_input(doc)


def test_missing_multiple_reported_in_template_order():
    doc = _doc(["Problem", "Users", "Goals"])
    assert missing_sections(doc) == [
        "Non-Goals", "Constraints", "Success Criteria", "Assumptions", "Open Questions",
    ]
    with pytest.raises(ProductInputError) as exc:
        validate_product_input(doc)
    msg = str(exc.value)
    assert "Non-Goals" in msg and "Open Questions" in msg
    assert "Required sections:" in msg


def test_empty_document_lists_all_missing():
    assert missing_sections("# Product Input — test\n") == ALL_SECTIONS


def test_present_but_empty_section_passes_structural_check():
    # Structural only: a header with no body is still present.
    doc = "\n".join(f"## {s}" for s in ALL_SECTIONS)
    validate_product_input(doc)  # no raise


def test_extra_sections_ignored():
    doc = _doc(ALL_SECTIONS + ["Risks", "Timeline"])
    validate_product_input(doc)  # extra sections are fine


def test_load_product_input(tmp_path):
    cfg = _config(tmp_path)
    write_artifact(cfg, "acme", PRODUCT_INPUT_FILENAME, _doc(ALL_SECTIONS))
    text = load_product_input(cfg, "acme")
    assert text.startswith("# Product Input")


def test_load_missing_file_raises(tmp_path):
    cfg = _config(tmp_path)
    with pytest.raises(ArtifactError, match="not found"):
        load_product_input(cfg, "acme")


def test_load_and_validate_roundtrip(tmp_path):
    cfg = _config(tmp_path)
    write_artifact(cfg, "acme", PRODUCT_INPUT_FILENAME, _doc(ALL_SECTIONS))
    assert load_and_validate(cfg, "acme").startswith("# Product Input")


def test_load_and_validate_rejects_incomplete(tmp_path):
    cfg = _config(tmp_path)
    write_artifact(cfg, "acme", PRODUCT_INPUT_FILENAME, _doc(["Problem", "Users"]))
    with pytest.raises(ProductInputError):
        load_and_validate(cfg, "acme")
