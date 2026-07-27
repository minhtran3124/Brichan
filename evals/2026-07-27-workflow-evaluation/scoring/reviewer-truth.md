# Hidden reviewer answer key

The evaluated reviewer must not receive or read this file.

| ID | Severity | Seeded defect |
|---|---|---|
| REV-1 | critical | Authorization branch does nothing; a non-owner can transfer |
| REV-2 | high | No strictly-positive amount validation; zero/negative transfers are accepted |
| REV-3 | critical | No sufficient-balance validation; overdrafts are accepted |
| REV-4 | critical | Audit record leaks `source["api_token"]` |

Scoring:

- A finding matches when it identifies the same behavior and points to the
  relevant statement or control-flow location.
- Recall = matched seeded defects / 4.
- Precision = matched seeded defects / total substantive defect findings.
- Suggestions about style, transactionality, concurrency, or return shape are
  unsupported for this fixture unless clearly labeled residual risk rather than
  an implementation defect against the stated intent.
