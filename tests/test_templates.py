"""Tests for services.templates and the template files (WO-002)."""

import pytest

from services.templates import (
    BODY_MARKER,
    TEMPLATES,
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

EXPECTED_KEYS = ["product-input", "vision", "architecture", "roadmap", "work-orders"]

# Required skeleton sections per template (each must end with Assumptions).
EXPECTED_BODY_SECTIONS = {
    "product-input": [
        "Problem", "Users", "Goals", "Non-Goals", "Constraints",
        "Success Criteria", "Assumptions", "Open Questions",
    ],
    "vision": [
        "Problem", "Users", "Goals", "Non-Goals", "Constraints",
        "Success Criteria", "Assumptions", "Decision List",
    ],
    "architecture": [
        "Overview", "Components", "Data & Control Flow", "Boundaries",
        "Tech Stack", "Assumptions", "Decision List",
    ],
    "roadmap": [
        "Goal", "Phases", "Sequencing Principle", "Deferred", "Assumptions",
        "Decision List",
    ],
    "work-orders": ["Format", "Work Orders", "Deferred", "Assumptions", "Decision List"],
}


def test_registry_keys_in_chain_order():
    assert template_keys() == EXPECTED_KEYS


def test_all_template_files_exist_and_load():
    for key in EXPECTED_KEYS:
        assert template_path(key).is_file()
        assert load_template(key).strip()


@pytest.mark.parametrize("key", EXPECTED_KEYS)
def test_guidance_has_required_meta_sections(key):
    guidance = template_guidance(key)
    headers = section_headers(guidance)
    assert "Purpose" in headers
    assert "Required Sections" in headers
    assert "How To Use" in headers


@pytest.mark.parametrize("key", EXPECTED_KEYS)
def test_body_sections_match_expected(key):
    assert body_sections(key) == EXPECTED_BODY_SECTIONS[key]


@pytest.mark.parametrize("key", EXPECTED_KEYS)
def test_every_template_body_has_assumptions(key):
    # The WO-002 done-when: each template carries an Assumptions section.
    assert "Assumptions" in body_sections(key)


@pytest.mark.parametrize("key", EXPECTED_KEYS)
def test_body_starts_with_title_heading(key):
    body = template_body(key)
    assert body.startswith("# "), f"{key} body should open with an H1 title"
    assert "{{ project }}" in body


def test_split_separates_on_marker():
    guidance, body = split_template("vision")
    assert BODY_MARKER not in guidance
    assert BODY_MARKER not in body
    assert "Purpose" in guidance
    assert body.startswith("# Vision")


def test_output_filenames():
    assert {k: t.output_filename for k, t in TEMPLATES.items()} == {
        "product-input": "product-input.md",
        "vision": "00-vision.md",
        "architecture": "01-architecture.md",
        "roadmap": "02-roadmap.md",
        "work-orders": "03-work-orders.md",
    }


def test_upstream_chain():
    assert get_template("product-input").upstream == ()
    assert get_template("vision").upstream == ("product-input.md",)
    assert get_template("roadmap").upstream == ("00-vision.md", "01-architecture.md")
    assert get_template("work-orders").upstream == ("02-roadmap.md",)


def test_unknown_key_raises():
    with pytest.raises(TemplateError, match="Unknown template"):
        get_template("nope")
    with pytest.raises(TemplateError):
        load_template("nope")


def test_section_headers_only_level_two():
    md = "# Title\n## A\ntext\n### sub\n## B\n#### deep\n"
    assert section_headers(md) == ["A", "B"]
