# Forgetting Policy — Deterministic Memory Lifecycle Management

---

## 1. Overview

The Forgetting Engine manages the lifecycle of memory entries by applying configurable policies that archive or remove stale, low-quality, or redundant entries. The CMS implements three deterministic forgetting policies — Age, Quality, and Duplicate — that run on demand or via the consolidation trigger. Forgetting is designed to be safe (never immediately deletes, preserves audit trail) and deterministic (fixed thresholds, no ML-based importance scoring).

---

## 2. Architecture

```
Forgetting Pipeline
  =====================================================================

  Trigger: engine.forget() (manual or scheduled)
     |
     v
  +-----------------------+
  | 1. Collect Active     |
  |    Entries            |
  +-----------------------+
     |
     +--> Policy 1: AgeThreshold
     |     |  entry.timestamp < now - aging_threshold_days
     |     v
     |     Candidates for archival
     |
     +--> Policy 2: QualityThreshold
     |     |  entry.quality_score < quality_threshold
     |     v
     |     Candidates for archival
     |
     +--> Policy 3: DuplicatePolicy
           |  entry.status == DELETED (post-consolidation)
           v
           Candidates for hard deletion
     |
     v
  +-----------------------+
  | 2. Archive Candidates |
  |    (change status to  |
  |     ARCHIVED)         |
  +-----------------------+
     |
     v
  +-----------------------+
  | 3. Delete Candidates  |
  |    (hard delete       |
  |     consolidated dupes)|
  +-----------------------+
     |
     v
  +-----------------------+
  | 4. Audit & Index      |
  |    Update             |
  +-----------------------+
```

---

## 3. Policy Definitions

### 3.1 Age Policy

```
Threshold: config.aging_threshold_days (default: 90)

For each active entry:
  age_days = (now - entry.timestamp).days
  if age_days > aging_threshold_days:
    if entry.quality_score >= quality_threshold:
      skip (high quality preserves entry)
    else:
      mark_for_archive(entry)

Score: calculate_age_score(entry) -> float
  age_days = (now - entry.timestamp).days
  return max(0.0, 1.0 - age_days / aging_threshold_days)
  # Score = 1.0 for new entries, 0.0 for entries past threshold
```

The age score is a linear decay function:

```
age_score = max(0.0, 1.0 - age_days / threshold_days)
```

| Age | Score (threshold=90) |
|---|---|
| 0 days | 1.00 |
| 30 days | 0.67 |
| 60 days | 0.33 |
| 90 days | 0.00 |
| 120 days | 0.00 (clamped) |

### 3.2 Quality Policy

```
Threshold: config.quality_threshold (default: 0.3)

For each active entry older than 7 days (grace period):
  if entry.quality_score < quality_threshold:
    mark_for_archive(entry)

Rationale: Low-quality entries degrade retrieval quality.
  Entries under 7 days old are exempt (grace period to allow quality accumulation).
```

### 3.3 Duplicate Policy

```
For each entry with status == DELETED (soft-deleted by consolidation):
  if entry was soft-deleted more than 24 hours ago (configurable):
    remove from store entirely (hard delete)
    remove from index

Rationale: Soft-deleted entries are kept temporarily for recovery,
  then permanently removed after a grace period.
```

---

## 4. Soft Deletion vs Hard Deletion

| Operation | Status Change | Data Loss | Recoverable | Use Case |
|---|---|---|---|---|
| Soft Delete | `ACTIVE` -> `DELETED` | None | Yes (change status back) | Consolidation, user-initiated delete |
| Archive | `ACTIVE` -> `ARCHIVED` | None | Yes (change status back) | Age/quality forgetting |
| Hard Delete | Removed from store | Full | No (unless from backup) | Duplicate cleanup after grace period |

---

## 5. Implementation

```python
class DefaultForgettingEngine(ForgettingEngine):
    def __init__(self, config: MemoryConfig):
        self.config = config

    def apply_policies(self, store: MemoryStore) -> list[str]:
        if not self.config.enable_forgetting:
            return []

        all_entries, _ = store.list_all(limit=100000)
        now = datetime.now()
        archived: list[str] = []
        deleted: list[str] = []

        # Age Policy
        if self.config.aging_threshold_days > 0:
            for entry in all_entries:
                if entry.status != MemoryStatus.ACTIVE:
                    continue
                age_days = (now - entry.timestamp).days
                if age_days > self.config.aging_threshold_days:
                    if entry.quality_score < self.config.quality_threshold:
                        entry.status = MemoryStatus.ARCHIVED
                        archived.append(entry.memory_id)
                    # High-quality old entries are preserved

        # Quality Policy
        for entry in all_entries:
            if entry.status != MemoryStatus.ACTIVE:
                continue
            age_days = (now - entry.timestamp).days
            if age_days > 7 and entry.quality_score < self.config.quality_threshold:
                entry.status = MemoryStatus.ARCHIVED
                archived.append(entry.memory_id)

        # Duplicate Policy (hard delete soft-deleted entries after grace period)
        for entry in all_entries:
            if entry.status == MemoryStatus.DELETED:
                age_days = (now - entry.timestamp).days
                if age_days > 1:  # 24-hour grace period
                    store.delete(entry.memory_id, soft=False)
                    deleted.append(entry.memory_id)

        return archived + deleted

    def calculate_age_score(self, entry: MemoryEntry) -> float:
        age_days = (datetime.now() - entry.timestamp).days
        if self.config.aging_threshold_days <= 0:
            return 1.0
        return max(0.0, 1.0 - age_days / self.config.aging_threshold_days)
```

---

## 6. Archive Workflow

```
Entry Status: ACTIVE
     |
     v (age or quality policy triggered)
Entry Status: ARCHIVED
     |
     +-- Outcome A: Retrieved by ID
     |     Engine.retrieve() returns entry (status check bypassed for direct ID lookup)
     |     User can "restore" by changing status back to ACTIVE
     |
     +-- Outcome B: Not retrieved
           Archived entries excluded from list_by_type, list_all, and search results
```

Archived entries are not returned by default queries but can be retrieved directly by ID. This provides a safety net: forgetting is reversible.

---

## 7. Configuration

| Parameter | Default | Policy | Description |
|---|---|---|---|
| `enable_forgetting` | True | All | Master switch |
| `aging_threshold_days` | 90 | Age | Days before age policy applies |
| `quality_threshold` | 0.3 | Quality, Age | Entries below this quality are archive candidates |
| `aging_threshold_days` = 0 | — | Age | Disables age policy |

---

## 8. Safety Guarantees

| Guarantee | Mechanism | Enforcement |
|---|---|---|
| Never immediate delete | Soft delete first; hard delete only after grace period | `delete(soft=True)` is default |
| Recoverable forgetting | Archived entries retrievable by ID | `store.retrieve()` bypasses status filter |
| Audit trail preserved | All forgetting events logged | `audit.log_access()` in pipeline |
| Quality preserves old entries | High-quality entries exempt from age policy | `quality_score >= quality_threshold` check |
| Grace period for new entries | Entries < 7 days exempt from quality policy | Age check in quality policy |

---

## 9. Examples

### Example 1: Manual Forgetting Trigger

```python
config = MemoryConfig(
    enable_forgetting=True,
    aging_threshold_days=90,
    quality_threshold=0.3,
)
engine = MemoryEngine(config=config)

# Trigger forgetting
forgotten_ids = engine.forget()
print(f"Archived {len(forgotten_ids)} entries")
for fid in forgotten_ids:
    entry = engine.retrieve(fid)
    print(f"  {fid}: status={entry.status}")
```

### Example 2: Age Score Calculation

```python
engine = DefaultForgettingEngine(config=MemoryConfig(aging_threshold_days=90))

# New entry
entry_new = MemoryEntry(timestamp=datetime.now(), ...)
score = engine.calculate_age_score(entry_new)  # 1.0

# Old entry
entry_old = MemoryEntry(timestamp=datetime.now() - timedelta(days=180), ...)
score = engine.calculate_age_score(entry_old)  # 0.0
```

### Example 3: Disabling Forgetting

```python
config = MemoryConfig(enable_forgetting=False)
engine = MemoryEngine(config=config)
forgotten = engine.forget()  # Returns [] immediately
```

---

## 10. Design Rationale

### Why Deterministic Forgetting

The CMS eschews ML-based forgetting (importance scoring, learned retention models) in favor of deterministic thresholds for three reasons:

| Reason | Explanation |
|---|---|
| Reproducibility | Fixed thresholds produce identical forgetting behavior across runs |
| Auditability | The rationale for each forgetting decision is transparent (age, quality, duplicate) |
| Predictability | System behavior is fully specified and testable |

### Why Not ML-Based Forgetting

ML-based forgetting (e.g., predicting which entries will be useful) would introduce non-determinism, require training data, and violate the CMS design principle of deterministic behavior. Future versions may add learned importance as an optional enrichment, but the core forgetting logic remains threshold-based.

---

## 11. Limitations

- Forgetting is triggered manually or via consolidation trigger; no background scheduler
- All entries are treated equally regardless of type (no per-type thresholds)
- No importance scoring beyond quality (no access-frequency boosted retention)
- No cascading forget (forgetting a parent does not automatically forget descendants)
- Age score is linear; no Ebbinghaus forgetting curve modeling

---

## 12. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- Consolidation: `MEMORY_CONSOLIDATION.md`
- Quality scoring: `QUALITY_SCORING.md`
- Audit: `AUDIT_SYSTEM.md`
- Engine source: `interfaces.py:221-229`
