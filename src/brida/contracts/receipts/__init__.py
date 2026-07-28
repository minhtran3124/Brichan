"""Canonical handoff-receipt schema, parsing, discovery, and validation."""

from .discovery import discover_receipts
from .parser import parse_receipt
from .validation import main, validate_projects, validate_receipt

__all__ = [
    "discover_receipts",
    "main",
    "parse_receipt",
    "validate_projects",
    "validate_receipt",
]
