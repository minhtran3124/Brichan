"""Receipt schema constants and parsed diagnostic types.

The validator remains the compatibility authority while these names provide a
stable import boundary for schema-aware callers.
"""

from .validation import (
    ATTEMPT_LIFECYCLE_STATES,
    ATTEMPT_ORIGINS,
    CRITERION_STATES,
    LIFECYCLE_STATES,
    PRIOR_ATTEMPT_STATES,
    RECEIPT_ROLES,
    REQUIRED_FIELDS,
    REQUIRED_SECTIONS,
    SCHEMA_V2_IDENTITY_FIELDS,
    VERIFICATION_STATES,
    Diagnostic,
    ParsedReceipt,
)

__all__ = [
    "ATTEMPT_LIFECYCLE_STATES",
    "ATTEMPT_ORIGINS",
    "CRITERION_STATES",
    "Diagnostic",
    "LIFECYCLE_STATES",
    "PRIOR_ATTEMPT_STATES",
    "ParsedReceipt",
    "RECEIPT_ROLES",
    "REQUIRED_FIELDS",
    "REQUIRED_SECTIONS",
    "SCHEMA_V2_IDENTITY_FIELDS",
    "VERIFICATION_STATES",
]
