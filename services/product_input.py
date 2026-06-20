"""Product Input intake (WO-002b).

Loads a project's ``product-input.md`` and validates it **structurally** against
the Product Input template (``08-product-input-template.md``, WO-002): every
required ``##`` section must be present. It does not judge content quality — an
empty-but-present section passes (that is the founder's job, and any agent's, not
intake's).

The required sections are sourced from the template registry
(:func:`services.templates.body_sections`) so there is one source of truth.
"""

from __future__ import annotations

from services import artifacts
from services.config import Config
from services.templates import body_sections, get_template, section_headers

# Single source of truth: the Product Input template's skeleton sections.
REQUIRED_SECTIONS: tuple[str, ...] = tuple(body_sections("product-input"))

# The artifact filename intake reads, per the template registry / D-008.
PRODUCT_INPUT_FILENAME = get_template("product-input").output_filename


class ProductInputError(RuntimeError):
    """Raised when a Product Input document fails structural validation."""


def missing_sections(markdown: str) -> list[str]:
    """Return the required sections absent from ``markdown``, in template order."""
    present = set(section_headers(markdown))
    return [s for s in REQUIRED_SECTIONS if s not in present]


def validate_product_input(markdown: str) -> None:
    """Validate that all required sections are present.

    Raises :class:`ProductInputError` listing every missing section if any are
    absent. Returns ``None`` on success.
    """
    missing = missing_sections(markdown)
    if missing:
        raise ProductInputError(
            "Product Input is missing required section(s): "
            + ", ".join(missing)
            + ". Required sections: "
            + ", ".join(REQUIRED_SECTIONS)
            + "."
        )


def load_product_input(config: Config, project: str) -> str:
    """Read a project's Product Input document without validating it.

    Raises :class:`services.artifacts.ArtifactError` if the file does not exist.
    """
    return artifacts.read_artifact(config, project, PRODUCT_INPUT_FILENAME)


def load_and_validate(config: Config, project: str) -> str:
    """Read and structurally validate a project's Product Input.

    Returns the document text on success. Raises
    :class:`services.artifacts.ArtifactError` if the file is missing, or
    :class:`ProductInputError` if required sections are absent.
    """
    text = load_product_input(config, project)
    validate_product_input(text)
    return text
