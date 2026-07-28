# Raw worker output excerpt — PILOT-003-T-R1

Captured from `brida-pilot-003-treatment-rerun` before pane cleanup.

```text
Task PILOT-003-T-R1 completed successfully. Exactly two pilot-tool read
receipt invocations were made (a first zero-effect attempt was aborted before
reaching the tool — see note below).

Call 1: stderr = PILOT003_FAULT_ONCE, exit = 42
Call 2: stdout = PILOT_TOOL_OK receipt, exit = 0

fault-bin/fault.log line count verified with wc -l = 1, content matches
expected command/exit/marker exactly.

Verified .fired/fault.log did not exist prior to the successful pair of calls,
confirming the one-shot fault fired exactly once and only on the intended first
call.

The first attempt redirected stderr to a root-level path and was rejected with
"read-only file system" before pilot-tool was invoked. The worker then checked
that .fired and fault.log were absent before making the two tool invocations.

No third invocation was made. No wrapper, receipt, or memory files were edited.
```

The complete wrapper output is stored separately in
`treatment-rerun-wrapper.log`; its one line is copied byte-for-byte from the
task-local wrapper before cleanup.
