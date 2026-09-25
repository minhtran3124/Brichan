"""Differential checks for T1: X vs Y ledger_summary on adversarial input."""
import os
import importlib.util
import sys

BASE = os.environ.get("WFS_REVIEW_DIR", "wfs-review")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


X = load("x_ledger", f"{BASE}/X/t1-ledger-summary/ledger_summary.py")
Y = load("y_ledger", f"{BASE}/Y/t1-ledger-summary/ledger_summary.py")

cases = {
    "deep_nesting": b"[" * 100000,
    "deep_nesting_dict": b'{"a":' * 50000,
    "empty": b"",
    "only_newlines": b"\n\n\n",
    "bare_cr_line": b'{"event": "launched", "launch_id": "a"}\r\n\r',
    "crlf_no_final_lf": b'{"event": "launched", "launch_id": "a"}\r\n{"event": "finished", "launch_id": "a"}\r',
    "bom_line": b'\xef\xbb\xbf{"event": "launched", "launch_id": "a"}',
    "dup_json_keys": b'{"event": "launched", "event": "finished", "launch_id": "a"}',
    "nan_ok": b'{"event": "launched", "launch_id": "a", "x": NaN}',
    "surrogate": b'{"event": "launched", "launch_id": "\\ud800"}',
    "finish_launch_finish": (
        b'{"event": "finished", "launch_id": "a"}\n'
        b'{"event": "launched", "launch_id": "a"}\n'
        b'{"event": "finished", "launch_id": "a"}\n'
    ),
    "orphan_dupes": (
        b'{"event": "finished", "launch_id": "y"}\n'
        b'{"event": "finished", "launch_id": "x"}\n'
        b'{"event": "finished", "launch_id": "y"}\n'
    ),
    "ws_around_json": b'   {"event": "launched", "launch_id": "a"}  \t',
}

for name, data in cases.items():
    results = {}
    for tag, mod in (("X", X), ("Y", Y)):
        try:
            results[tag] = mod.summarize(data)
        except Exception as exc:  # noqa: BLE001
            results[tag] = f"RAISED {type(exc).__name__}: {str(exc)[:60]}"
    marker = "SAME" if results["X"] == results["Y"] else "DIFF"
    print(f"[{marker}] {name}")
    if marker == "DIFF":
        print(f"    X: {results['X']}")
        print(f"    Y: {results['Y']}")
    else:
        print(f"    both: {results['X']}")
