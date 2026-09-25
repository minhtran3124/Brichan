# T3: accept redundant path segments (contract-sensitive edit)

`path_guard.validate_ledger_path(value)` guards a user-supplied, relative
ledger path before the program writes to it. Users report that
`ledger/./workers.jsonl` and `ledger//workers.jsonl` are rejected even though
they obviously mean `ledger/workers.jsonl`.

Change `validate_ledger_path` so that it accepts redundant `.` components and
repeated `/` separators, and returns the normalized path (components joined by
a single `/`, with empty and `.` components removed).

Every security invariant documented in the module docstring must keep
holding. Keep the signature and the `ValueError` type for rejections. Update
the docstring and add tests.

Standard library only.
