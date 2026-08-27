.PHONY: help release-preview test test-unit test-contract test-integration techstack-eval metrics receipts dossiers memory-check path-check readme-check phase5-preflight package-check contract-check check

PYTHON ?= python3

help:
	@echo "Brichan repository commands:"
	@echo "  make test           Run all Python test layers"
	@echo "  make test-unit      Run importable-core unit tests"
	@echo "  make test-contract  Run repository and durable-contract tests"
	@echo "  make test-integration Run stable-wrapper integration tests"
	@echo "  make techstack-eval Run the frozen techstack context evaluation"
	@echo "  make metrics        Validate and summarize the metrics ledger"
	@echo "  make receipts       Validate canonical handoff receipts"
	@echo "  make dossiers       Validate checkout-mode task dossiers"
	@echo "  make memory-check   Validate durable project-memory consistency"
	@echo "  make path-check     Validate repository paths and local Markdown links"
	@echo "  make readme-check   Rebuild and validate the PyPI long description"
	@echo "  make phase5-preflight Report compatibility-pointer retirement eligibility"
	@echo "  make package-check  Compile and import the source package"
	@echo "  make contract-check Check launcher syntax and repository contracts"
	@echo "  make check          Run the complete local validation"
	@echo "  make release-preview Verify and build a PyPI release without uploading"

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

techstack-eval:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest evals.techstack_context_v1.test_cases -v

metrics:
	$(PYTHON) metrics/validate_metrics.py metrics/runs.jsonl
	$(PYTHON) metrics/validate_metrics.py metrics/runs.jsonl --summary

receipts:
	$(PYTHON) scripts/validate_handoff_receipts.py projects

dossiers:
	$(PYTHON) scripts/validate_task_dossiers.py projects

memory-check:
	$(PYTHON) scripts/check_project_memory.py

path-check:
	$(PYTHON) scripts/check_repository_paths.py

readme-check:
	$(PYTHON) scripts/build_pypi_readme.py --check

release-preview:
	$(PYTHON) scripts/release_pypi.py

phase5-preflight:
	$(PYTHON) scripts/check_compatibility_retirement.py

package-check:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) -c "import brichan.cli.provider_commands"
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) -c "import brichan.orchestration; import sys; assert not any(name == 'brichan.cli' or name.startswith('brichan.cli.') for name in sys.modules)"
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PYTHON) -c "import brichan; from brichan.contracts.receipts import validation; from brichan.orchestration import worker_launch"

contract-check: path-check test-contract
	sh -n bin/brichan

check: test techstack-eval metrics receipts dossiers memory-check path-check readme-check phase5-preflight package-check
	sh -n bin/brichan
