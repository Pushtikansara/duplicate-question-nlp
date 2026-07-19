from __future__ import annotations

import pytest

from duplicate_question_app._models.registry import ModelRegistryEntry, build_registry


class TestModelRegistry:
    def test_registry_entry_creation(self):
        entry = ModelRegistryEntry(
            display_name="Test Model",
            internal_id="test",
            model_type="transformer",
            framework="pytorch",
            source="huggingface",
            version="1.0",
            local_path="/tmp/model",
            cache_path=None,
            device="cpu",
            size_mb=100.0,
            load_status="not_loaded",
            is_loaded=False,
            has_artifacts=True,
        )
        assert entry.display_name == "Test Model"
        assert entry.internal_id == "test"
        assert entry.model_type == "transformer"

    def test_registry_entry_defaults(self):
        entry = ModelRegistryEntry(
            display_name="Default Model",
            internal_id="default",
            model_type="embedding",
            framework="sentence-transformers",
            source="huggingface",
            version="1.0",
            local_path="/tmp/model",
            cache_path=None,
            device="cpu",
            size_mb=50.0,
            load_status="not_loaded",
            is_loaded=False,
            has_artifacts=False,
        )
        assert entry.parameters == "N/A"
        assert entry.embedding_size is None
        assert entry.accuracy is None

    def test_build_registry_returns_list(self):
        registry = build_registry()
        assert isinstance(registry, list)
        assert len(registry) > 0

    def test_build_registry_contains_expected_models(self):
        registry = build_registry()
        names = [e.display_name for e in registry]
        assert "E5-base-v2" in names
        assert "BGE-base-en-v1.5" in names

    def test_build_registry_entries_have_ids(self):
        registry = build_registry()
        for entry in registry:
            assert entry.internal_id, f"Entry {entry.display_name} missing internal_id"

    def test_build_registry_model_types(self):
        registry = build_registry()
        types = {e.model_type for e in registry}
        assert "transformer" in types or "embedding" in types or "ensemble" in types

    def test_build_registry_no_duplicate_display_names(self):
        registry = build_registry()
        names = [e.display_name for e in registry]
        assert len(names) == len(set(names))

    def test_registry_min_length(self):
        registry = build_registry()
        assert len(registry) >= 9

    def test_registry_entry_load_status(self):
        entry = ModelRegistryEntry(
            display_name="Test", internal_id="t", model_type="t", framework="f",
            source="s", version="1", local_path="/p", cache_path=None, device="cpu",
            size_mb=1, load_status="loaded", is_loaded=True, has_artifacts=True,
        )
        assert entry.load_status == "loaded"
        assert entry.is_loaded is True

    def test_registry_importable_from_stub(self):
        from duplicate_question_app.model_registry import ModelRegistryEntry as StubEntry
        assert StubEntry is ModelRegistryEntry

    def test_build_registry_orders_consistently(self):
        r1 = build_registry()
        r2 = build_registry()
        names1 = [e.display_name for e in r1]
        names2 = [e.display_name for e in r2]
        assert names1 == names2
