# T1: summarize a worker ledger (implementation)

Implement `summarize(data: bytes) -> dict` in `ledger_summary.py`.

`data` is a JSONL ledger: UTF-8, one JSON object per line, lines separated by
`\n`. Each record has at least `event` (`"launched"` or `"finished"`) and
`launch_id` (string). Other keys may exist and must be ignored.

Rules:

1. Lines that are empty or contain only whitespace are ignored and are **not**
   counted anywhere.
2. Any other line that is not a JSON object with a string `event` and a string
   `launch_id` is skipped and counted in `undecodable`. This includes invalid
   UTF-8, invalid JSON, JSON that is not an object, and objects missing either
   key or holding a non-string value for it. Lines with an `event` value other
   than `launched`/`finished` are also counted in `undecodable`.
3. Records pair by `launch_id` only. Never join by `worker` or `pane_id`.
4. The first `finished` record for a `launch_id` in file order wins. Every
   later `finished` record for the same `launch_id` is counted in
   `duplicate_finished`.
5. A `finished` record whose `launch_id` has no `launched` record anywhere in
   the file (before or after) is an orphan, listed in `orphans`.
6. A `launch_id` with a `launched` record and no `finished` record is
   `unknown` — never "running" or "failed".
7. If the same `launch_id` has more than one `launched` record, only the first
   counts; later ones are counted in `duplicate_launched`.
8. The final line may lack a trailing `\n`; treat it as a line. A trailing `\r`
   before `\n` is part of the line content and must not make an otherwise
   valid record undecodable (JSON allows surrounding whitespace).

Return exactly these keys:

```python
{
    "finished": [launch_id, ...],   # launched and finished, in order of their launched record
    "unknown": [launch_id, ...],    # launched, never finished, in order of their launched record
    "orphans": [launch_id, ...],    # finished without launched, first occurrence order, no repeats
    "undecodable": int,
    "duplicate_finished": int,
    "duplicate_launched": int,
}
```

Standard library only. Do not change the function signature.
