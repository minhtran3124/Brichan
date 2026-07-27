import importlib.util
import sys
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "brida-herdr-agent-start"
LOADER = SourceFileLoader("brida_herdr_layout", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def pane(pane_id, x, y, width, height, focused=False):
    return {
        "pane_id": pane_id,
        "focused": focused,
        "rect": {"x": x, "y": y, "width": width, "height": height},
    }


def split(split_id, direction, ratio, x, y, width, height):
    return {
        "id": split_id,
        "direction": direction,
        "ratio": ratio,
        "rect": {"x": x, "y": y, "width": width, "height": height},
    }


class HerdrLayoutPlannerTest(unittest.TestCase):
    def test_cli_accepts_herdr_style_name_then_options(self):
        args = MODULE._parse_args(
            [
                "brida-review",
                "--anchor-pane",
                "w1:p1",
                "--cwd",
                "/tmp/project",
                "--",
                "codex",
                "--disable",
                "multi_agent",
            ]
        )

        self.assertEqual("brida-review", args.name)
        self.assertEqual("w1:p1", args.anchor_pane)
        self.assertEqual("/tmp/project", args.cwd)
        self.assertEqual(["codex", "--disable", "multi_agent"], args.argv)

    def test_first_worker_splits_coordinator_and_worker_evenly(self):
        layout = {
            "panes": [pane("p1", 0, 0, 240, 80, True)],
            "splits": [],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual("p1", plan.target_pane_id)
        self.assertEqual("right", plan.split)
        self.assertEqual((), plan.pre_resizes)
        self.assertEqual((), plan.post_resizes)
        self.assertTrue(plan.exact_equal_area)

    def test_second_worker_produces_three_equal_area_panes(self):
        layout = {
            "panes": [
                pane("p1", 0, 0, 120, 80, True),
                pane("p2", 120, 0, 120, 80),
            ],
            "splits": [split("root", "right", 0.5, 0, 0, 240, 80)],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual("p1", plan.target_pane_id)
        self.assertEqual("down", plan.split)
        self.assertEqual("right", plan.post_resizes[0].direction)
        self.assertAlmostEqual(1 / 6, plan.post_resizes[0].amount)
        self.assertTrue(plan.exact_equal_area)

    def test_second_worker_shrinks_an_oversized_anchor_side(self):
        layout = {
            "panes": [
                pane("p1", 0, 0, 192, 80, True),
                pane("p2", 192, 0, 48, 80),
            ],
            "splits": [split("root", "right", 0.8, 0, 0, 240, 80)],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual("left", plan.post_resizes[0].direction)
        self.assertAlmostEqual(0.8 - 2 / 3, plan.post_resizes[0].amount)

    def test_second_worker_handles_anchor_on_second_side(self):
        layout = {
            "panes": [
                pane("p2", 0, 0, 120, 80),
                pane("p1", 120, 0, 120, 80, True),
            ],
            "splits": [split("root", "right", 0.5, 0, 0, 240, 80)],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual("p2", plan.post_resizes[0].pane_id)
        self.assertEqual("left", plan.post_resizes[0].direction)
        self.assertAlmostEqual(1 / 6, plan.post_resizes[0].amount)

    def test_third_worker_produces_two_by_two_grid(self):
        layout = {
            "panes": [
                pane("p1", 0, 0, 160, 40, True),
                pane("p3", 0, 40, 160, 40),
                pane("p2", 160, 0, 80, 80),
            ],
            "splits": [
                split("root", "right", 2 / 3, 0, 0, 240, 80),
                split("left", "down", 0.5, 0, 0, 160, 80),
            ],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual("p2", plan.target_pane_id)
        self.assertEqual("down", plan.split)
        self.assertEqual("left", plan.pre_resizes[0].direction)
        self.assertAlmostEqual(1 / 6, plan.pre_resizes[0].amount)
        self.assertEqual((), plan.post_resizes)
        self.assertTrue(plan.exact_equal_area)

    def test_third_worker_normalizes_uneven_inner_split(self):
        layout = {
            "panes": [
                pane("p1", 0, 0, 160, 24, True),
                pane("p3", 0, 24, 160, 56),
                pane("p2", 160, 0, 80, 80),
            ],
            "splits": [
                split("root", "right", 2 / 3, 0, 0, 240, 80),
                split("left", "down", 0.3, 0, 0, 160, 80),
            ],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual(2, len(plan.pre_resizes))
        self.assertEqual("left", plan.pre_resizes[0].direction)
        self.assertEqual("down", plan.pre_resizes[1].direction)
        self.assertAlmostEqual(0.2, plan.pre_resizes[1].amount)

    def test_vertical_root_uses_horizontal_inner_split(self):
        layout = {
            "panes": [
                pane("p1", 0, 0, 240, 40, True),
                pane("p2", 0, 40, 240, 40),
            ],
            "splits": [split("root", "down", 0.5, 0, 0, 240, 80)],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual("right", plan.split)
        self.assertEqual("down", plan.post_resizes[0].direction)

    def test_noncanonical_layout_splits_largest_pane_best_effort(self):
        layout = {
            "panes": [
                pane("p1", 0, 0, 30, 80, True),
                pane("p2", 30, 0, 60, 80),
                pane("p3", 90, 0, 150, 80),
            ],
            "splits": [
                split("root", "right", 0.375, 0, 0, 240, 80),
                split("left", "right", 1 / 3, 0, 0, 90, 80),
            ],
        }

        plan = MODULE.plan_spawn(layout, "p1")

        self.assertEqual("p3", plan.target_pane_id)
        self.assertEqual("right", plan.split)
        self.assertFalse(plan.exact_equal_area)


if __name__ == "__main__":
    unittest.main()
