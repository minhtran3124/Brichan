#!/usr/bin/env python3
"""Start a Herdr worker while keeping the coordinator tab visually balanced."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .model_routing import (
    ResolvedRoute,
    RoutingError,
    load_settings,
    resolve_route,
)
class HerdrError(RuntimeError):
    """Raised when a Herdr command cannot be completed."""


@dataclass(frozen=True)
class ResizeOp:
    pane_id: str
    direction: str
    amount: float


@dataclass(frozen=True)
class SpawnPlan:
    target_pane_id: str
    split: str
    pre_resizes: tuple[ResizeOp, ...] = ()
    post_resizes: tuple[ResizeOp, ...] = ()
    exact_equal_area: bool = True


@dataclass(frozen=True)
class LaunchResolution:
    command: tuple[str, ...]
    route_name: str | None = None
    route: ResolvedRoute | None = None


def _run_json(argv: list[str]) -> tuple[dict[str, Any], str]:
    result = subprocess.run(argv, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise HerdrError(f"{' '.join(argv)} failed: {detail}")
    try:
        return json.loads(result.stdout), result.stdout
    except json.JSONDecodeError as exc:
        raise HerdrError(f"{' '.join(argv)} returned invalid JSON") from exc


def _layout(anchor_pane_id: str) -> dict[str, Any]:
    payload, _ = _run_json(
        ["herdr", "pane", "layout", "--pane", anchor_pane_id]
    )
    return payload["result"]["layout"]


def _pane_center(pane: dict[str, Any]) -> tuple[float, float]:
    rect = pane["rect"]
    return (
        rect["x"] + rect["width"] / 2,
        rect["y"] + rect["height"] / 2,
    )


def _root_split(layout: dict[str, Any]) -> dict[str, Any]:
    splits = layout.get("splits", [])
    if not splits:
        raise ValueError("layout has no split")
    return max(
        splits,
        key=lambda split: split["rect"]["width"] * split["rect"]["height"],
    )


def _members(
    split: dict[str, Any], panes: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rect = split["rect"]
    if split["direction"] == "right":
        boundary = rect["x"] + rect["width"] * split["ratio"]
        first = [pane for pane in panes if _pane_center(pane)[0] < boundary]
    else:
        boundary = rect["y"] + rect["height"] * split["ratio"]
        first = [pane for pane in panes if _pane_center(pane)[1] < boundary]
    first_ids = {pane["pane_id"] for pane in first}
    second = [pane for pane in panes if pane["pane_id"] not in first_ids]
    return first, second


def _opposite(direction: str) -> str:
    return {
        "right": "left",
        "left": "right",
        "down": "up",
        "up": "down",
    }[direction]


def _perpendicular(direction: str) -> str:
    return "down" if direction == "right" else "right"


def _resize_first_side(
    split: dict[str, Any],
    first: list[dict[str, Any]],
    target_ratio: float,
) -> ResizeOp | None:
    delta = target_ratio - split["ratio"]
    if abs(delta) <= 0.0001:
        return None
    return ResizeOp(
        pane_id=first[0]["pane_id"],
        direction=split["direction"] if delta > 0 else _opposite(split["direction"]),
        amount=abs(delta),
    )


def _split_is_within_group(
    split: dict[str, Any], group: list[dict[str, Any]]
) -> bool:
    rect = split["rect"]
    center = (
        rect["x"] + rect["width"] / 2,
        rect["y"] + rect["height"] / 2,
    )
    return any(
        pane["rect"]["x"] <= center[0] <= pane["rect"]["x"] + pane["rect"]["width"]
        and pane["rect"]["y"]
        <= center[1]
        <= pane["rect"]["y"] + pane["rect"]["height"]
        for pane in group
    )


def plan_spawn(layout: dict[str, Any], anchor_pane_id: str) -> SpawnPlan:
    """Return the balancing operations for coordinator plus the next worker."""

    panes = layout["panes"]
    pane_by_id = {pane["pane_id"]: pane for pane in panes}
    if anchor_pane_id not in pane_by_id:
        raise ValueError(f"anchor pane {anchor_pane_id} is not in the tab")

    if len(panes) == 1:
        return SpawnPlan(anchor_pane_id, "right")

    root = _root_split(layout)
    first, second = _members(root, panes)
    first_ids = {pane["pane_id"] for pane in first}

    if len(panes) == 2 and len(first) == len(second) == 1:
        anchor_is_first = anchor_pane_id in first_ids
        target_ratio = 2 / 3 if anchor_is_first else 1 / 3
        resize = _resize_first_side(root, first, target_ratio)
        return SpawnPlan(
            target_pane_id=anchor_pane_id,
            split=_perpendicular(root["direction"]),
            post_resizes=(resize,) if resize else (),
        )

    if len(panes) == 3:
        anchor_group = first if anchor_pane_id in first_ids else second
        other_group = second if anchor_pane_id in first_ids else first
        inner_splits = [
            split
            for split in layout["splits"]
            if split["id"] != root["id"]
            and _split_is_within_group(split, anchor_group)
        ]
        if len(anchor_group) == 2 and len(other_group) == 1 and len(inner_splits) == 1:
            inner = inner_splits[0]
            inner_first, inner_second = _members(inner, anchor_group)
            if (
                inner["direction"] != root["direction"]
                and len(inner_first) == len(inner_second) == 1
            ):
                root_resize = _resize_first_side(root, first, 0.5)
                inner_resize = _resize_first_side(inner, inner_first, 0.5)
                pre_resizes = tuple(
                    resize
                    for resize in (root_resize, inner_resize)
                    if resize is not None
                )
                return SpawnPlan(
                    target_pane_id=other_group[0]["pane_id"],
                    split=inner["direction"],
                    pre_resizes=pre_resizes,
                )

    largest = max(
        panes,
        key=lambda pane: pane["rect"]["width"] * pane["rect"]["height"],
    )
    rect = largest["rect"]
    split = "right" if rect["width"] >= rect["height"] else "down"
    return SpawnPlan(
        target_pane_id=largest["pane_id"],
        split=split,
        exact_equal_area=False,
    )


def _focus_pane(anchor_pane_id: str, target_pane_id: str) -> None:
    for _ in range(16):
        layout = _layout(anchor_pane_id)
        focused_id = layout["focused_pane_id"]
        if focused_id == target_pane_id:
            return

        panes = {pane["pane_id"]: pane for pane in layout["panes"]}
        current = panes[focused_id]
        target = panes[target_pane_id]
        current_x, current_y = _pane_center(current)
        target_x, target_y = _pane_center(target)
        horizontal = "right" if target_x > current_x else "left"
        vertical = "down" if target_y > current_y else "up"
        directions = (
            (horizontal, vertical)
            if abs(target_x - current_x) >= abs(target_y - current_y)
            else (vertical, horizontal)
        )

        moved = False
        for direction in directions:
            payload, _ = _run_json(
                [
                    "herdr",
                    "pane",
                    "focus",
                    "--pane",
                    focused_id,
                    "--direction",
                    direction,
                ]
            )
            next_id = payload["result"]["focus"]["focused_pane_id"]
            if next_id != focused_id:
                moved = True
                break
        if not moved:
            break
    raise HerdrError(f"could not focus pane {target_pane_id}")


def _resize(op: ResizeOp) -> None:
    if op.amount <= 0.0001:
        return
    _run_json(
        [
            "herdr",
            "pane",
            "resize",
            "--pane",
            op.pane_id,
            "--direction",
            op.direction,
            "--amount",
            f"{op.amount:.7f}",
        ]
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw_argv = sys.argv[1:] if argv is None else argv
    try:
        separator = raw_argv.index("--")
    except ValueError:
        separator = -1
    if separator < 0:
        launcher_argv = raw_argv
        agent_argv: list[str] = []
    else:
        launcher_argv = raw_argv[:separator]
        agent_argv = raw_argv[separator + 1 :]

    parser = argparse.ArgumentParser(
        description=(
            "Start a Brichan-owned Herdr agent and balance the coordinator tab. "
            "Layouts with up to four total panes receive equal area."
        )
    )
    parser.add_argument("name")
    parser.add_argument("--anchor-pane")
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--route")
    parser.add_argument("--runtime")
    parser.add_argument("--model")
    parser.add_argument("--effort")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="resolve and validate the worker command without calling Herdr",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="emit machine-readable resolution JSON; implies --dry-run",
    )
    args = parser.parse_args(launcher_argv)
    args.argv = agent_argv
    if not args.name.startswith("brichan-"):
        parser.error("agent name must begin with brichan-")
    if args.route and agent_argv:
        parser.error("--route cannot be combined with a legacy command after --")
    if not args.route and not agent_argv:
        parser.error("use --route NAME or provide a legacy agent command after --")
    if not args.route and any((args.runtime, args.model, args.effort)):
        parser.error("--runtime, --model, and --effort require --route")
    if args.json_output:
        args.dry_run = True
    if not args.dry_run and not args.anchor_pane:
        parser.error("--anchor-pane is required unless --dry-run or --json is used")
    return args


def _resolve_launch(args: argparse.Namespace) -> LaunchResolution:
    if args.route:
        # Keep the orchestration package provider-neutral at import time.  The
        # CLI adapter is needed only after a named route has been resolved.
        from brichan.cli.provider_commands import worker_command

        target_root = Path(args.cwd).expanduser().resolve()
        target_state = target_root / ".brichan"
        if os.path.lexists(target_state):
            from brichan.lifecycle import StateKind, inspect_project
            from brichan.project import project_paths

            paths = project_paths(explicit=target_root)
            inspection = inspect_project(paths)
            if inspection.kind is not StateKind.HEALTHY:
                raise RoutingError(
                    f"target project state is {inspection.kind.value}: "
                    f"{inspection.detail}"
                )
            settings = load_settings(
                paths.state_root / "config" / "model-routing.json"
            )
        else:
            settings = load_settings(repository=target_root)
        route = resolve_route(
            settings,
            args.route,
            runtime=args.runtime,
            model=args.model,
            effort=args.effort,
        )
        return LaunchResolution(
            command=tuple(worker_command(route)),
            route_name=args.route,
            route=route,
        )
    # Legacy commands need the provider guard only when that compatibility
    # path is selected, not while importing orchestration primitives.
    from brichan.cli.provider_commands import secure_legacy_command

    return LaunchResolution(command=tuple(secure_legacy_command(args.argv)))


def _print_dry_run(
    args: argparse.Namespace,
    resolution: LaunchResolution,
) -> None:
    if args.json_output:
        payload = {
            "dry_run": True,
            "name": args.name,
            "cwd": args.cwd,
            "route": resolution.route_name,
            "resolved": (
                resolution.route.as_dict() if resolution.route is not None else None
            ),
            "command": list(resolution.command),
            "legacy_explicit_command": resolution.route_name is None,
        }
        print(json.dumps(payload, sort_keys=True))
        return
    print(shlex.join(resolution.command))


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        resolution = _resolve_launch(args)
        if args.dry_run:
            _print_dry_run(args, resolution)
            return 0

        anchor_payload, _ = _run_json(
            ["herdr", "pane", "get", args.anchor_pane]
        )
        anchor = anchor_payload["result"]["pane"]
        layout = _layout(args.anchor_pane)
        plan = plan_spawn(layout, args.anchor_pane)

        if not plan.exact_equal_area:
            print(
                "warning: more than four or non-canonical panes; "
                "splitting the largest pane as a best effort",
                file=sys.stderr,
            )

        applied_pre_resizes: list[ResizeOp] = []
        try:
            for resize in plan.pre_resizes:
                _resize(resize)
                applied_pre_resizes.append(resize)
            _focus_pane(args.anchor_pane, plan.target_pane_id)

            command = [
                "herdr",
                "agent",
                "start",
                args.name,
                "--workspace",
                anchor["workspace_id"],
                "--tab",
                anchor["tab_id"],
                "--split",
                plan.split,
                "--cwd",
                args.cwd,
                "--no-focus",
            ]
            for item in args.env:
                command.extend(["--env", item])
            command.append("--")
            command.extend(resolution.command)

            start_payload, start_stdout = _run_json(command)
        except HerdrError:
            for resize in reversed(applied_pre_resizes):
                try:
                    _resize(
                        ResizeOp(
                            pane_id=resize.pane_id,
                            direction=_opposite(resize.direction),
                            amount=resize.amount,
                        )
                    )
                except HerdrError:
                    pass
            try:
                _focus_pane(args.anchor_pane, args.anchor_pane)
            except HerdrError:
                pass
            raise

        for resize in plan.post_resizes:
            try:
                _resize(resize)
            except HerdrError as exc:
                print(f"warning: worker started but layout resize failed: {exc}", file=sys.stderr)
        try:
            _focus_pane(args.anchor_pane, args.anchor_pane)
        except HerdrError as exc:
            print(f"warning: worker started but focus restore failed: {exc}", file=sys.stderr)

        if start_payload["result"]["agent"]["pane_id"] == args.anchor_pane:
            raise HerdrError("Herdr reused the coordinator pane unexpectedly")
        sys.stdout.write(start_stdout)
        return 0
    except (HerdrError, KeyError, RoutingError, ValueError) as exc:
        print(f"brichan-herdr-agent-start: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
