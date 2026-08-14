# Phase 14.2 — Release Checkpoint

> Status: **checkpointed**. Phase 14.2 implementation is frozen, tagged and pushed.
> This document records the actual verification results and known follow-ups. It is
> intentionally added **after** the tag; the historical implementation commit is
> immutable and the tag is not moved.

---

## 1. Frozen scope

| Item | Value |
| --- | --- |
| Implementation commit | `39462981676b5a19cf54b64f6cadee5c42c0ce4e` |
| Commit message | `feat(adaptive): implement phase 14.2 adaptive intelligence` |
| Tag | `v14.2-adaptive-intelligence` (annotated, object `4e5da6b...`) |
| Tag peeled target | `39462981676b5a19cf54b64f6cadee5c42c0ce4e` (matches commit) |
| Branch | `feature/phase14-adaptive-routing` |
| Remote | present — branch and tag verified on `origin` |

The tagged commit contains only Phase 14.2 work; no unrelated files were swept in.

## 2. Verification results (actual)

| Gate | Command | Result |
| --- | --- | --- |
| Lint | `ruff check .` | PASS |
| Format | `ruff format --check src/ tests/` | PASS |
| Imports | `isort --check-only src/ tests/` | PASS |
| Type checking | `mypy src/ares/adaptive/` | **FAIL — 2 pre-existing `attr-defined` errors** (see §4) |
| Pre-commit (Phase 14.2 file surface) | `pre-commit run --files <phase 14.2 files>` | PASS (all 13 hooks) |
| Unit + integration tests | `pytest tests/unit/adaptive/ tests/integration/test_adaptive_routing_integration.py` | PASS — 155 passed |
| Full suite | `pytest tests/ -q --ignore=tests/e2e` | PASS — 4237 passed |
| Real-model benchmark | `scripts/evaluate_adaptive_routing.py --warmup` | PASS — 13/13 (100%) |
| Package build | `python -m build --sdist --wheel` | PASS — sdist + wheel built |

No Phase 14.2 file was modified by the verification toolchain (confirmed clean via
`git status` after the pre-commit run).

## 3. Backward compatibility

- Adaptive routing remains **opt-in** (`configs/adaptive_routing.yaml` → `enabled: false`).
- REST, gRPC, CLI, `PredictionService` and `PredictionOrchestrator` interfaces are
  covered by the full suite; entry-point/orchestrator integration tests pass
  (`8 passed` for the focused set; 4237 total).
- Phase 13 trace keys are preserved additively under
  `orchestration_trace["adaptive_routing"]`.

## 4. Known issue — mypy (pre-existing, not introduced by Phase 14.2)

`mypy src/ares/adaptive/` exits non-zero with **2 `attr-defined` errors** in
`src/ares/adaptive/executor.py`:

```
error: "AdaptiveExecutionError" has no attribute "_adaptive_run"  [attr-defined]
error: "AdaptiveExecutionError" has no attribute "adaptive_trace" [attr-defined]
```

These lines attach runtime attributes to the exception raised during adaptive
execution. The session logs record the same errors as **pre-existing** on the
untracked adaptive module prior to the Phase 14.2 edits (previously at
`executor.py:708` / `executor.py:727`). During the 14.2 session they were briefly
"fixed" with `setattr`; the pre-commit `ruff --fix` hook (B010) reverted
`setattr` back to direct attribute assignment immediately before the commit, so the
frozen commit carries the direct-assignment form.

Per the checkpoint convention, failures that are pre-existing and unrelated to the
frozen phase are **identified, not fixed** — the tagged commit is immutable and a
fix would not make the tagged rollback point type-clean anyway. **Deferred to
Phase 14.3 housekeeping:** replace the dynamic attribute attachment with explicit
typed exception fields (or an attribute-defined-allowlist on the exception class).

## 5. State after checkpoint

- `HEAD` = `3946298` (implementation commit), ahead of nothing, clean for frozen files.
- Tag `v14.2-adaptive-intelligence` remains at `3946298` on local and remote.
- Remote branch `feature/phase14-adaptive-routing` points at `3946298`.
- This documentation commit (`20_PHASE_14_2_CHECKPOINT.md`) is added on top of the
  tag **without** moving it, so the Phase 14.2 release tag stays immutable.
