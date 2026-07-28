.PHONY: help test metrics receipts contract-check check

PYTHON ?= python3

help:
	@echo "Brida repository commands:"
	@echo "  make test           Run all Python tests"
	@echo "  make metrics        Validate and summarize the metrics ledger"
	@echo "  make receipts       Validate canonical handoff receipts"
	@echo "  make contract-check Check launcher syntax and repository contracts"
	@echo "  make check          Run the complete local validation"

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest metrics/test_validate_metrics.py -v
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -v

metrics:
	$(PYTHON) metrics/validate_metrics.py metrics/runs.jsonl
	$(PYTHON) metrics/validate_metrics.py metrics/runs.jsonl --summary

receipts:
	$(PYTHON) scripts/validate_handoff_receipts.py projects

contract-check:
	sh -n bin/brida
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -v

check: test metrics receipts
	sh -n bin/brida
