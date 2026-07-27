#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "task_id",
    "track",
    "started_at",
    "completed_at",
    "elapsed_seconds",
    "verdict",
    "acceptance_passed",
    "acceptance_total",
    "worker_count",
    "blocker_count",
    "user_intervention_count",
    "reviewer_finding_count",
    "coordinator_input_tokens",
    "coordinator_output_tokens",
    "worker_input_tokens",
    "worker_output_tokens",
    "cost_usd",
    "cost_source",
    "evidence",
    "notes",
}
NONNEGATIVE_INTS = {
    "acceptance_passed",
    "acceptance_total",
    "worker_count",
    "blocker_count",
    "user_intervention_count",
    "reviewer_finding_count",
}
NULLABLE_NONNEGATIVE_INTS = {
    "coordinator_input_tokens",
    "coordinator_output_tokens",
    "worker_input_tokens",
    "worker_output_tokens",
}


def _parse_timestamp(value, field, errors):
    if value is None:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        errors.append(f"{field} must be null or a UTC timestamp ending in Z")
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        errors.append(f"{field} is not valid ISO 8601")
        return None


def validate_row(row, line_number):
    errors = []
    if not isinstance(row, dict):
        return [f"line {line_number}: row must be a JSON object"]

    missing = sorted(REQUIRED_FIELDS - row.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
        return [f"line {line_number}: {error}" for error in errors]

    if row["schema_version"] != 1:
        errors.append("schema_version must be 1")
    for field in ("run_id", "task_id", "track", "notes"):
        if not isinstance(row[field], str) or not row[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if row["verdict"] not in {"PASS", "PARTIAL", "FAIL"}:
        errors.append("verdict must be PASS, PARTIAL, or FAIL")

    started_at = _parse_timestamp(row["started_at"], "started_at", errors)
    completed_at = _parse_timestamp(row["completed_at"], "completed_at", errors)
    if (started_at is None) != (completed_at is None):
        errors.append("started_at and completed_at must both be observed or both be null")
    if started_at is not None and completed_at is not None and completed_at < started_at:
        errors.append("completed_at cannot precede started_at")

    elapsed = row["elapsed_seconds"]
    if elapsed is not None and (
        isinstance(elapsed, bool)
        or not isinstance(elapsed, (int, float))
        or elapsed < 0
    ):
        errors.append("elapsed_seconds must be null or a non-negative number")

    for field in NONNEGATIVE_INTS:
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"{field} must be a non-negative integer")

    if (
        isinstance(row["acceptance_passed"], int)
        and isinstance(row["acceptance_total"], int)
        and row["acceptance_passed"] > row["acceptance_total"]
    ):
        errors.append("acceptance_passed cannot exceed acceptance_total")
    if (
        row["verdict"] == "PASS"
        and isinstance(row["acceptance_passed"], int)
        and isinstance(row["acceptance_total"], int)
        and row["acceptance_passed"] != row["acceptance_total"]
    ):
        errors.append("PASS requires all acceptance checks to pass")

    for field in NULLABLE_NONNEGATIVE_INTS:
        value = row[field]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            errors.append(f"{field} must be null or a non-negative integer")
    if row["worker_count"] == 0 and any(
        row[field] is not None
        for field in ("worker_input_tokens", "worker_output_tokens")
    ):
        errors.append("worker token fields must be null when worker_count is zero")

    cost = row["cost_usd"]
    if cost is not None and (
        isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0
    ):
        errors.append("cost_usd must be null or a non-negative number")
    if cost is None and row["cost_source"] is not None:
        errors.append("cost_source must be null when cost_usd is null")
    if cost is not None and (
        not isinstance(row["cost_source"], str) or not row["cost_source"].strip()
    ):
        errors.append("cost_source is required when cost_usd is present")

    evidence = row["evidence"]
    if (
        not isinstance(evidence, list)
        or not evidence
        or any(not isinstance(item, str) or not item.strip() for item in evidence)
    ):
        errors.append("evidence must be a non-empty array of strings")

    return [f"line {line_number}: {error}" for error in errors]


def load_rows(path):
    rows = []
    errors = []
    seen_run_ids = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
            continue
        errors.extend(validate_row(row, line_number))
        if isinstance(row, dict) and isinstance(row.get("run_id"), str):
            if row["run_id"] in seen_run_ids:
                errors.append(f"line {line_number}: duplicate run_id {row['run_id']}")
            seen_run_ids.add(row["run_id"])
        rows.append(row)
    if not rows:
        errors.append("ledger contains no rows")
    return rows, errors


def render_summary(rows):
    valid_rows = [row for row in rows if isinstance(row, dict)]
    verdicts = {name: 0 for name in ("PASS", "PARTIAL", "FAIL")}
    for row in valid_rows:
        verdict = row.get("verdict")
        if verdict in verdicts:
            verdicts[verdict] += 1

    token_fields = (
        "coordinator_input_tokens",
        "coordinator_output_tokens",
        "worker_input_tokens",
        "worker_output_tokens",
    )
    observed_tokens = {}
    observed_token_rows = {}
    for field in token_fields:
        values = [row.get(field) for row in valid_rows if row.get(field) is not None]
        observed_tokens[field] = sum(values)
        observed_token_rows[field] = len(values)
    unknown_token_rows = sum(
        1
        for row in valid_rows
        if any(row.get(field) is None for field in token_fields)
    )

    return "\n".join(
        [
            f"runs={len(valid_rows)}",
            "verdicts=" + ",".join(f"{key}:{verdicts[key]}" for key in verdicts),
            f"workers={sum(row.get('worker_count', 0) for row in valid_rows)}",
            f"blockers={sum(row.get('blocker_count', 0) for row in valid_rows)}",
            "acceptance="
            + f"{sum(row.get('acceptance_passed', 0) for row in valid_rows)}"
            + "/"
            + f"{sum(row.get('acceptance_total', 0) for row in valid_rows)}",
            "tokens="
            + ",".join(
                f"{field}:{observed_tokens[field]}/{observed_token_rows[field]}obs"
                for field in token_fields
            ),
            f"unknown_token_rows={unknown_token_rows}",
            "cost_observed_rows="
            + str(sum(1 for row in valid_rows if row.get("cost_usd") is not None)),
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    rows, errors = load_rows(args.ledger)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if args.summary:
        print(render_summary(rows))
    else:
        print(f"valid: {len(rows)} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
