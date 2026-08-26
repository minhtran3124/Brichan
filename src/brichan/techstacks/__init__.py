"""Read-only project-owned techstack context.

The package exposes the frozen public model surface. It imports no CLI module,
no project-memory module, and no evaluation module, so importing a record never
loads a command surface.

Design sections 2 and 16 place ``verify_snapshot`` and ``publish_snapshot`` on
that surface, and both live in the one module that owns a command surface. They
are therefore resolved lazily through the PEP 562 module ``__getattr__`` below,
so naming them imports the CLI module while merely importing this package still
does not.
"""

from typing import Any

from .model import (
    DIAGNOSTIC_CODES,
    DIAGNOSTIC_REGISTRY,
    DIFFERENCE_CODES,
    FIXED_DETAILS,
    INPUT_ERROR_CODES,
    PUBLICATION_DOCUMENT_BYTE_LIMIT,
    ROOT_API_OUTCOMES,
    SCHEMA_VERSION,
    SNAPSHOT_DOCUMENT_BYTE_LIMIT,
    SNAPSHOT_ERROR_CODES,
    SNAPSHOT_ROOT_MAP,
    DeclaredConflict,
    Diagnostic,
    Difference,
    EffectiveRule,
    EvidenceObservation,
    ExceptionApproval,
    FailureTarget,
    FileIdentity,
    Resolution,
    ResolutionInput,
    RootIdentity,
    SelectedFile,
    Snapshot,
    SnapshotAttempt,
    SnapshotPublication,
    TechstackError,
    TechstackInputError,
    TechstackSnapshotError,
    Totals,
    Verification,
    canonical_json_document,
    canonical_json_text,
    publication_document,
    snapshot_digest,
    snapshot_document,
)
from .resolver import resolve_context

__all__ = [
    "DIAGNOSTIC_CODES",
    "DIAGNOSTIC_REGISTRY",
    "DIFFERENCE_CODES",
    "DeclaredConflict",
    "Diagnostic",
    "Difference",
    "EffectiveRule",
    "EvidenceObservation",
    "ExceptionApproval",
    "FIXED_DETAILS",
    "FailureTarget",
    "FileIdentity",
    "INPUT_ERROR_CODES",
    "PUBLICATION_DOCUMENT_BYTE_LIMIT",
    "ROOT_API_OUTCOMES",
    "Resolution",
    "ResolutionInput",
    "RootIdentity",
    "SCHEMA_VERSION",
    "SNAPSHOT_DOCUMENT_BYTE_LIMIT",
    "SNAPSHOT_ERROR_CODES",
    "SNAPSHOT_ROOT_MAP",
    "SelectedFile",
    "Snapshot",
    "SnapshotAttempt",
    "SnapshotPublication",
    "TechstackError",
    "TechstackInputError",
    "TechstackSnapshotError",
    "Totals",
    "Verification",
    "canonical_json_document",
    "canonical_json_text",
    "publication_document",
    "publish_snapshot",
    "resolve_context",
    "snapshot_digest",
    "snapshot_document",
    "verify_snapshot",
]

#: The two public names that live in the CLI module, resolved on first access.
_LAZY_EXPORTS = ("publish_snapshot", "verify_snapshot")


def __getattr__(name: str) -> Any:
    """Resolve the two CLI-owned public names without importing them eagerly."""

    if name in _LAZY_EXPORTS:
        from . import cli

        value = getattr(cli, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """List the default module names plus ``__all__``, so the lazy names show."""

    return sorted(set(globals()) | set(__all__))
