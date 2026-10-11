"""Differential and adversarial checks comparing submissions X and Y.

Run from the repo root:
    python3 wfs010-review/scratch/diff_checks.py
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(sub, task, module):
    path = ROOT / sub / task / f"{module}.py"
    spec = importlib.util.spec_from_file_location(f"{sub}_{module}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(label, fn):
    try:
        result = fn()
        print(f"{label}: {result!r}")
    except Exception as exc:
        print(f"{label}: raised {type(exc).__name__}: {exc}")


# ---- T1: ledger summary ----
x1 = load("X", "t1-ledger-summary", "ledger_summary")
y1 = load("Y", "t1-ledger-summary", "ledger_summary")

deep = b"[" * 20000 + b"\n" + b'{"event": "launched", "launch_id": "a"}\n'
check("T1 X deep-nesting line", lambda: x1.summarize(deep))
check("T1 Y deep-nesting line", lambda: y1.summarize(deep))

nbsp = b"\xc2\xa0\n" + b'{"event": "launched", "launch_id": "a"}\n'
check("T1 X NBSP-only line", lambda: x1.summarize(nbsp))
check("T1 Y NBSP-only line", lambda: y1.summarize(nbsp))

# ---- T2: semver ----
x2 = load("X", "t2-prerelease-order", "semver_order")
y2 = load("Y", "t2-prerelease-order", "semver_order")

for bad in ["1.0.0\n", "1٢.0.0", "1.0.0-rc.1٢", "1.0.0-rc.1\n"]:
    check(f"T2 X parse({bad!r})", lambda b=bad: x2.parse(b))
    check(f"T2 Y parse({bad!r})", lambda b=bad: y2.parse(b))

check("T2 X compare('1.0.0\\n','1.0.0')", lambda: x2.compare("1.0.0\n", "1.0.0"))

# agreement sweep on valid versions
versions = [
    "0.0.1", "0.9.9", "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta",
    "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0-rc.2",
    "1.0.0-rc.10", "1.0.0", "1.0.1", "1.9.0", "1.10.0", "2.0.0-0",
    "2.0.0-0.1", "2.0.0-Z", "2.0.0-a", "2.0.0-a-", "2.0.0-a0", "2.0.0-1a",
    "2.0.0--", "2.0.0", "2.0.0+build.1",
]
disagree = [
    (a, b)
    for a in versions
    for b in versions
    if x2.compare(a, b) != y2.compare(a, b)
]
print(f"T2 X/Y compare disagreements over {len(versions)}^2 valid versions: {disagree}")

# ---- T3: path guard ----
x3 = load("X", "t3-path-guard", "path_guard")
y3 = load("Y", "t3-path-guard", "path_guard")

cases = [
    "ledger/./workers.jsonl", "ledger//workers.jsonl", "./ledger/workers.jsonl",
    "ledger/workers.jsonl/", "ledger/workers.jsonl/.", "ledger/workers.jsonl//",
    "ledger/.//../workers.jsonl", "a/./.BriChan//x.jsonl", ".", "./", "",
    "workers.jsonl", "a/..jsonl", "x.jsonl/./", ".jsonl",
]
for value in cases:
    check(f"T3 X {value!r}", lambda v=value: x3.validate_ledger_path(v))
    check(f"T3 Y {value!r}", lambda v=value: y3.validate_ledger_path(v))
