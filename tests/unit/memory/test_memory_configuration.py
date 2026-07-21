from __future__ import annotations

from duplicate_question_app._memory.memory_configuration import MemoryConfig, MemoryConfigLoader


class TestMemoryConfiguration:
    def test_default_config(self) -> None:
        config = MemoryConfig()
        assert config.max_entries == 10000
        assert config.max_versions == 10
        assert config.default_ttl_days == 365
        assert config.enable_consolidation is True
        assert config.enable_audit is True
        assert config.enable_forgetting is True

    def test_custom_config(self) -> None:
        config = MemoryConfig(
            max_entries=500,
            max_versions=3,
            default_ttl_days=30,
            enable_consolidation=False,
        )
        assert config.max_entries == 500
        assert config.max_versions == 3
        assert config.default_ttl_days == 30
        assert config.enable_consolidation is False

    def test_from_dict(self) -> None:
        data = {
            "max_entries": 2000,
            "max_versions": 5,
            "default_ttl_days": 90,
            "enable_consolidation": False,
            "enable_audit": True,
            "enable_forgetting": False,
            "auto_consolidate_interval": 500,
            "aging_threshold_days": 30,
            "quality_threshold": 0.5,
            "confidence_threshold": 0.4,
            "store_type": "in_memory",
        }
        config = MemoryConfigLoader.from_dict(data)
        assert config.max_entries == 2000
        assert config.max_versions == 5
        assert config.aging_threshold_days == 30
        assert config.quality_threshold == 0.5

    def test_from_dict_partial(self) -> None:
        data = {"max_entries": 500}
        config = MemoryConfigLoader.from_dict(data)
        assert config.max_entries == 500
        assert config.max_versions == 10

    def test_config_limits(self) -> None:
        config = MemoryConfig(max_entries=100, max_versions=3)
        assert config.max_entries == 100
        assert config.max_versions == 3

    def test_config_thresholds(self) -> None:
        config = MemoryConfig(
            quality_threshold=0.7,
            confidence_threshold=0.6,
        )
        assert config.quality_threshold == 0.7
        assert config.confidence_threshold == 0.6

    def test_config_ttl(self) -> None:
        config = MemoryConfig(default_ttl_days=14)
        assert config.default_ttl_days == 14

    def test_config_flags(self) -> None:
        config = MemoryConfig(
            enable_consolidation=False,
            enable_audit=False,
            enable_forgetting=False,
        )
        assert config.enable_consolidation is False
        assert config.enable_audit is False
        assert config.enable_forgetting is False

    def test_config_loader_default(self) -> None:
        config = MemoryConfigLoader.load_default()
        assert isinstance(config, MemoryConfig)
        assert config.max_entries == 10000

    def test_config_loader_from_dict(self) -> None:
        data = {"store_type": "custom"}
        config = MemoryConfigLoader.from_dict(data)
        assert config.store_type == "custom"
