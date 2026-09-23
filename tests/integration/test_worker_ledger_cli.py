"""The ledger's storage invariant and its two command entry points.

Two things are pinned here that unit tests cannot own. The first is R8: an
installed project carrying a ledger must stay exactly as healthy as one
without it, because a future extra-entries check in project inspection would
otherwise break every ledger-bearing project silently. The second is the
command surface: a console-script or wrapper typo is invisible to unit tests,
so the committed wrapper is run end to end.
"""

import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRICHAN = ROOT / "bin/brichan"
LEDGER_WRAPPER = ROOT / "bin/brichan-herdr-worker-ledger"


class LedgerCliTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_path = Path(self.temporary.name).resolve()

    def environment(self):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return environment

    def run_brichan(self, *arguments):
        return subprocess.run(
            [str(BRICHAN), *arguments],
            cwd=self.temp_path,
            env=self.environment(),
            check=False,
            capture_output=True,
            text=True,
        )

    def initialized_project(self, name="target"):
        project = self.temp_path / name
        project.mkdir()
        result = subprocess.run(
            ["git", "init", "--quiet", str(project)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        result = self.run_brichan("init", "--apply", "--project", str(project))
        self.assertEqual(0, result.returncode, result.stderr)
        return project


class LedgerStorageInvariantTest(LedgerCliTestCase):
    """R8: the chosen storage location must be inert to project inspection.

    Project inspection validates only enumerated paths and never lists the
    state directory's contents, so an unnamed entry is never examined. That is
    the load-bearing claim of the storage decision; without a regression test
    the one-off reproduction would never notice it breaking.
    """

    def test_a_ledger_leaves_status_doctor_and_init_exactly_as_they_were(self):
        project = self.initialized_project()

        before_status = self.run_brichan("status", "--project", str(project))
        before_doctor = self.run_brichan(
            "doctor", "--json", "--project", str(project)
        )
        before_init = self.run_brichan("init", "--project", str(project))
        self.assertEqual(0, before_status.returncode, before_status.stderr)
        # Doctor's installed exit is owned by state plus Codex availability:
        # 0 when Codex is present, 4 when it is not (as on CI runners). Either
        # way the state is healthy; the before/after equality below is the
        # invariant under test.
        self.assertIn(before_doctor.returncode, (0, 4), before_doctor.stderr)

        ledger = project / ".brichan/ledger/workers.jsonl"
        ledger.parent.mkdir()
        ledger.write_text(
            json.dumps({"schema_version": 1, "event": "launched"}) + "\n",
            encoding="utf-8",
        )

        after_status = self.run_brichan("status", "--project", str(project))
        after_doctor = self.run_brichan(
            "doctor", "--json", "--project", str(project)
        )
        after_init = self.run_brichan("init", "--project", str(project))

        self.assertIn("healthy", after_status.stdout)
        self.assertEqual(before_status.returncode, after_status.returncode)
        self.assertEqual(before_status.stdout, after_status.stdout)
        self.assertEqual(before_doctor.returncode, after_doctor.returncode)
        self.assertEqual(before_doctor.stdout, after_doctor.stdout)
        self.assertEqual(before_init.returncode, after_init.returncode)
        self.assertEqual(before_init.stdout, after_init.stdout)


class InstalledFinishTest(LedgerCliTestCase):
    """R9 end to end: the guard is what keeps a target project healthy.

    A partial `.brichan` without `manifest.json` is diagnosed `malformed`, so a
    ledger command that created one would break the project it was recording.
    Deleting the guard must fail these tests.
    """

    def setUp(self):
        super().setUp()
        self.installed = self.temp_path / "installed-worker-ledger"
        self.installed.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
            "from brichan.orchestration.worker_ledger import main\n"
            "raise SystemExit(main())\n",
            encoding="utf-8",
        )
        self.installed.chmod(self.installed.stat().st_mode | stat.S_IXUSR)

    def run_installed(self, *arguments, environment=None):
        return subprocess.run(
            [str(self.installed), *arguments],
            cwd=self.temp_path,
            env=self.environment() if environment is None else environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_a_target_without_managed_state_is_refused_and_gets_nothing(self):
        bare = self.temp_path / "bare"
        bare.mkdir()
        subprocess.run(
            ["git", "init", "--quiet", str(bare)], check=True, capture_output=True
        )

        result = self.run_installed(
            "finish",
            "--worker",
            "brichan-worker",
            "--launch-id",
            "launch-1",
            "--evidence",
            "projects/x/handoffs/T/implementation.md",
            "--project",
            str(bare),
        )

        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("no ledger for this target", result.stderr)
        self.assertFalse((bare / ".brichan").exists())

    def test_the_installed_entrypoint_ignores_a_checkout_claim(self):
        """`SCRIPT-002`: mode is a property of the launch, not the environment.

        An installed console script that honoured `BRICHAN_ROOT` would switch
        ledger location based on an exported variable.
        """

        project = self.initialized_project()
        environment = self.environment()
        environment["BRICHAN_ROOT"] = str(self.temp_path / "not-a-checkout")

        result = self.run_installed(
            "finish",
            "--worker",
            "brichan-worker",
            "--launch-id",
            "launch-absent",
            "--evidence",
            "projects/x/handoffs/T/implementation.md",
            "--project",
            str(project),
            environment=environment,
        )

        # The target's own fixed ledger was consulted, so the refusal is the
        # unmatched identifier and never a redirected location.
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn("no launched record", result.stderr)
        self.assertFalse((self.temp_path / "not-a-checkout").exists())


class CheckoutWrapperTest(LedgerCliTestCase):
    """The committed wrapper is the compatibility contract layer.

    A console-script or import typo in `bin/` is invisible to unit tests, so
    the wrapper itself is copied byte for byte into a throwaway checkout and
    run end to end.
    """

    def setUp(self):
        super().setUp()
        self.checkout = self.temp_path / "checkout"
        (self.checkout / "bin").mkdir(parents=True)
        (self.checkout / "projects" / "slug").mkdir(parents=True)
        os.symlink(ROOT / "src", self.checkout / "src")
        self.wrapper = self.checkout / LEDGER_WRAPPER.name
        shutil.copy2(LEDGER_WRAPPER, self.checkout / "bin" / LEDGER_WRAPPER.name)
        self.wrapper = self.checkout / "bin" / LEDGER_WRAPPER.name
        self.ledger_value = "projects/slug/ledger/workers.jsonl"
        self.ledger_path = self.checkout / self.ledger_value
        self.ledger_path.parent.mkdir()
        self.ledger_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "event": "launched",
                    "launch_id": "launch-1",
                    "worker": "brichan-worker",
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def run_wrapper(self, *arguments):
        return subprocess.run(
            [str(self.wrapper), *arguments],
            cwd=self.checkout,
            env=self.environment(),
            check=False,
            capture_output=True,
            text=True,
        )

    def records(self):
        return [
            json.loads(line)
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_the_wrapper_appends_one_finished_attestation(self):
        result = self.run_wrapper(
            "finish",
            "--worker",
            "brichan-worker",
            "--launch-id",
            "launch-1",
            "--evidence",
            "projects/x/handoffs/T/implementation.md",
            "--evidence",
            "make check",
            "--ledger-file",
            self.ledger_value,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        record = self.records()[-1]
        self.assertEqual("finished", record["event"])
        self.assertEqual("launch-1", record["launch_id"])
        self.assertEqual(
            ["projects/x/handoffs/T/implementation.md", "make check"],
            record["evidence"],
        )
        self.assertEqual("coordinator", record["source"])

    def test_the_wrapper_refuses_a_second_attestation_for_one_launch(self):
        arguments = (
            "finish",
            "--worker",
            "brichan-worker",
            "--launch-id",
            "launch-1",
            "--evidence",
            "projects/x/handoffs/T/implementation.md",
            "--ledger-file",
            self.ledger_value,
        )
        self.assertEqual(0, self.run_wrapper(*arguments).returncode)
        after_first = self.ledger_path.read_bytes()

        result = self.run_wrapper(*arguments)

        self.assertEqual(1, result.returncode)
        self.assertIn("already has a finished record", result.stderr)
        self.assertEqual(after_first, self.ledger_path.read_bytes())

    def test_the_wrapper_refuses_a_managed_state_ledger_file(self):
        result = self.run_wrapper(
            "finish",
            "--worker",
            "brichan-worker",
            "--launch-id",
            "launch-1",
            "--evidence",
            "e",
            "--ledger-file",
            ".BRICHAN/ledger/workers.jsonl",
        )

        self.assertEqual(2, result.returncode)
        self.assertFalse((self.checkout / ".brichan").exists())
        self.assertFalse((self.checkout / ".BRICHAN").exists())


if __name__ == "__main__":
    unittest.main()
