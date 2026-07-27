# Memory Validation — Phase 10.5.5

## Capacity Limits

| Tier | Capacity |
|------|----------|
| WORKING | 500 |
| SHORT_TERM | 1000 |
| LONG_TERM | 5000 |

## Eviction Policy

FIFO (First In, First Out) — oldest entries in the tier are evicted first when capacity is exceeded.

```python
# DEFAULT_TIER_CAPACITIES in store.py
MemoryTier.WORKING: 500
MemoryTier.SHORT_TERM: 1000
MemoryTier.LONG_TERM: 5000
```

## TTL Sweep

`MemoryStore.sweep_expired()`:
- Checks each in-memory entry's `ttl_seconds` against current time
- Removes expired entries
- Tracks eviction count via `MetricsRegistry`

## Statistics

`MemoryStats` now includes `eviction_count` field.

| Stat | Source |
|------|--------|
| Total entries | `get_stats().total_entries` |
| By tier | `get_stats().entries_by_tier` |
| By domain | `get_stats().entries_by_domain` |
| Eviction count | `get_stats().eviction_count` |
| Oldest entry | `get_stats().oldest_entry` |

## Edge Cases

- Custom capacities via `tier_capacities` parameter
- No eviction below capacity
- Per-tier eviction (not cross-tier)
- Zero-capacity tiers evict every new entry
