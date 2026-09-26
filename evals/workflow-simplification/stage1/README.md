# Stage 1 fixtures

Three seeded tasks for the `claude-opus-5` vs `claude-opus-5-5` benchmark in
`../protocol.md`. Each task directory holds a `TASK.md` specification, a
starter module, and a small visible test file. Hidden acceptance tests are
kept outside worker worktrees until both arms finish, then added under
`hidden/` with the results.

Run visible tests for one task:

    python3 -m unittest discover -s evals/workflow-simplification/stage1/<task> -p 'test_*.py' -v
