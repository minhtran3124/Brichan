.PHONY: help test test-unit test-contract test-integration metrics receipts path-check phase5-preflight package-check contract-check check

PYTHON ?= python3

help:
	@echo "Brida repository commands:"
	@echo "  make test           Run all Python test layers"
	@echo "  make test-unit      Run importable-core unit tests"
	@echo "  make test-contract  Run repository and durable-contract tests"
	@echo "  make test-integration Run stable-wrapper integration tests"
	@echo "  make metrics        Validate and summarize the metrics ledger"
	@echo "  make receipts       Validate canonical handoff receipts"
	@echo "  make path-check     Validate repository paths and local Markdown links"
	@echo "  make phase5-preflight Report compatibility-pointer retirement eligibility"
	@echo "  make package-check  Compile and import the source package"
	@echo "  make contract-check Check launcher syntax and repository contracts"
	@echo "  make check          Run the complete local validation"

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest metrics/test_validate_metrics.py -v
	$(MAKE) test-unit
	$(MAKE) test-contract
	$(MAKE) test-integration

test-unit:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests/unit -t . -v

test-contract:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests/contract -t . -v

test-integration:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests/integration -t . -v

metrics:
	$(PYTHON) metrics/validate_metrics.py metrics/runs.jsonl
	$(PYTHON) metrics/validate_metrics.py metrics/runs.jsonl --summary

receipts:
	$(PYTHON) scripts/validate_handoff_receipts.py projects

path-check:
	$(PYTHON) scripts/check_repository_paths.py

phase5-preflight:
	$(PYTHON) scripts/check_compatibility_retirement.py

package-check:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) -c "import brida.cli.provider_commands"
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) -c "import brida.orchestration; import sys; assert not any(name == 'brida.cli' or name.startswith('brida.cli.') for name in sys.modules)"
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) -c "import brida; from brida.contracts.receipts import validation; from brida.orchestration import worker_launch"

contract-check: path-check test-contract
	sh -n bin/brida

check: test metrics receipts path-check phase5-preflight package-check
	sh -n bin/brida
