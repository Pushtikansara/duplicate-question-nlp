from __future__ import annotations

from duplicate_question_app._integration.integration_configuration import IntegrationConfig


class TestIntegrationConfig:
    def test_default_config(self):
        config = IntegrationConfig()
        assert config.enable_perception is True
        assert config.enable_routing is True
        assert config.enable_memory_read is True
        assert config.enable_semantic is True
        assert config.enable_reasoning is True
        assert config.enable_debate is True
        assert config.enable_memory_write is True
        assert config.fail_on_perception_error is False

    def test_custom_config(self):
        config = IntegrationConfig(
            enable_perception=False,
            enable_memory_read=False,
        )
        assert config.enable_perception is False
        assert config.enable_memory_read is False
        assert config.enable_routing is True
