"""Differential checks for T3: X vs Y path_guard."""
import os
import importlib.util
import itertools
import random

BASE = os.environ.get("WFS_REVIEW_DIR", "wfs-review")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


X = load("x_guard", f"{BASE}/X/t3-path-guard/path_guard.py")
Y = load("y_guard", f"{BASE}/Y/t3-path-guard/path_guard.py")


def call(mod, v):
    try:
        return mod.validate_ledger_path(v)
    except ValueError:
        return "ValueError"
    except Exception as exc:  # noqa: BLE001
        return f"RAISED {type(exc).__name__}"


cases = [
    "ledger/./workers.jsonl", "ledger//workers.jsonl", "workers.jsonl",
    "./workers.jsonl", "ledger/workers.jsonl/", "ledger/workers.jsonl//",
    "ledger/workers.jsonl/.", "ledger/workers.jsonl/./", "a.jsonl/./.",
    "", ".", "./", "//", "/a.jsonl", "//a.jsonl", "/./a.jsonl",
    "../a.jsonl", "a/../b.jsonl", "a/../../b.jsonl", "a.jsonl/..",
    ".brichan/a.jsonl", "a/.BRICHAN/b.jsonl", "a/./.brichan//b.jsonl",
    ".brichan-old/a.jsonl", ".brichan./a.jsonl", "a\\b.jsonl", "a\x00b.jsonl",
    "a.JSONL", "a.json", "a/.jsonl", "a//.jsonl", "...jsonl", "..a/b.jsonl",
    "a.jsonl/b", "a.jsonl/./b", " /a.jsonl", "a b/c d.jsonl", "a.jsonl ",
    "⁄a.jsonl", "a\u0000.jsonl",
]

diffs = []
for v in cases:
    rx, ry = call(X, v), call(Y, v)
    mark = "SAME" if rx == ry else "DIFF"
    if mark == "DIFF":
        diffs.append(v)
    print(f"[{mark}] {v!r:40} X={rx!r:30} Y={ry!r}")

# Fuzz: check both never return a path violating the invariants.
random.seed(3)
ALPH = ["a", "b", ".", "/", "..", ".jsonl", ".brichan", ".BriChan", "", "\\", "\x00", "jsonl"]
violations = 0
disagreements = 0
for _ in range(300000):
    v = "".join(random.choice(ALPH) for _ in range(random.randint(1, 6)))
    rx, ry = call(X, v), call(Y, v)
    for tag, res in (("X", rx), ("Y", ry)):
        if isinstance(res, str) and not res.startswith(("ValueError", "RAISED")):
            parts = res.split("/")
            ok = (
                res
                and not res.startswith("/")
                and "\\" not in res and "\x00" not in res
                and all(p not in ("", ".", "..") for p in parts)
                and all(p.lower() != ".brichan" for p in parts)
                and parts[-1].endswith(".jsonl")
            )
            if not ok:
                violations += 1
                print(f"INVARIANT VIOLATION {tag}: {v!r} -> {res!r}")
    if (rx == "ValueError") != (ry == "ValueError"):
        disagreements += 1
        if disagreements <= 15:
            print(f"ACCEPT/REJECT DIFF: {v!r}: X={rx!r} Y={ry!r}")
    elif rx != ry:
        print(f"VALUE DIFF: {v!r}: X={rx!r} Y={ry!r}")
print(f"fuzz: {violations} invariant violations, {disagreements} accept/reject differences")
