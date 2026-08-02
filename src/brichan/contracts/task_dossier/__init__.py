"""Checkout-mode full-document task-dossier contract, scaffold, and validator."""

from .generate import (
    apply_generation,
    main as generate_main,
    plan_generation,
    render_artifact,
)
from .record import ArtifactRecord, TaskRecord, load_record
from .scaffold import (
    ScaffoldAction,
    apply_scaffold,
    dossier_path,
    plan_scaffold,
    template_path,
    template_text,
)
from .summary import (
    DossierSummary,
    main as summary_main,
    render_summary_json,
    render_summary_text,
    summarize_dossier,
)
from .validation import (
    discover_dossiers,
    discover_partial_dossiers,
    main,
    validate_dossier,
    validate_projects,
)

__all__ = [
    "ArtifactRecord",
    "DossierSummary",
    "ScaffoldAction",
    "TaskRecord",
    "apply_generation",
    "apply_scaffold",
    "discover_dossiers",
    "discover_partial_dossiers",
    "dossier_path",
    "generate_main",
    "load_record",
    "main",
    "plan_generation",
    "plan_scaffold",
    "render_artifact",
    "render_summary_json",
    "render_summary_text",
    "summarize_dossier",
    "summary_main",
    "template_path",
    "template_text",
    "validate_dossier",
    "validate_projects",
]
