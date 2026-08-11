from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import pytest
from fastapi.testclient import TestClient

from ares.api.app import create_app
from ares.api.config import APIConfig, Settings
from ares.api.models import UserRole
from ares.api.security import SecurityManager
from ares.model_registry import ModelCapabilities, ModelEntry, ModelHealth


class _MockPredictionResult(dict):
    """Acts as both a dict (for API handlers) and a PredictionResult-like object (for gRPC)."""

    def __init__(self):
        raw = {
            "predicted_label": 1,
            "prediction": "duplicate",
            "confidence": 0.95,
            "prob_duplicate": 0.95,
            "prob_non_duplicate": 0.05,
            "model_label": "test-model",
            "latency_ms": 10.5,
            "threshold": 0.5,
            "trust_score": 0.9,
            "trust_level": "high",
            "risk_level": "low",
            "model_name": "test-model",
            "explanation": "",
            "recommendations": [],
            "evidence": [],
            "consistency_check": None,
            "confidence_audit": None,
        }
        super().__init__(raw)
        self.raw = raw
        self.predicted_label = 1
        self.prediction = "duplicate"
        self.confidence = 0.95
        self.prob_duplicate = 0.95
        self.prob_non_duplicate = 0.05
        self.model_name = "test-model"
        self.latency_ms = 10.5
        self.threshold = 0.5
        self.trust_score = 0.9
        self.trust_level = "high"
        self.risk_level = "low"
        self.human_review_required = False
        self.recommendations = []
        self.explanations = {}

    def to_dict(self):
        return dict(self.raw)


def _make_mock_engine():
    engine = MagicMock()
    prediction = _MockPredictionResult()
    engine.predict.return_value = prediction
    engine.predict_batch.return_value = [prediction]
    engine.with_model.return_value = engine
    engine.with_threshold.return_value = engine
    engine.with_reflection.return_value = engine
    engine.with_semantic_validation.return_value = engine
    engine.with_fusion_mode.return_value = engine
    engine.reflect.return_value = {
        "trust_score": 0.9,
        "trust_level": "high",
        "risk_level": "low",
        "confidence": 0.95,
        "explanation": "",
        "recommendations": [],
        "evidence": [],
        "confidence_audit": None,
        "consistency_check": None,
    }
    return engine


@pytest.fixture(autouse=True)
def _patch_ares_engine():
    """Replace ARES class with a mock so no real model loading occurs.

    The mock is bound in every namespace that constructs the engine,
    including the Phase 13 orchestration engine adapter (the canonical
    engine path for all entry points) so that entry-point tests exercise
    the orchestrator pipeline without touching real model artifacts.
    """
    mock_engine = _make_mock_engine()
    mock_ares_class = MagicMock(return_value=mock_engine)
    with (
        patch("ares._engine.ARES", mock_ares_class),
        patch("ares.ARES", mock_ares_class),
        patch("ares.orchestration.engine_adapter.ARES", mock_ares_class),
    ):
        yield


@pytest.fixture(autouse=True)
def _patch_torch_cuda():
    """Prevent CUDA checks from failing."""
    with patch("torch.cuda.is_available", return_value=False):
        yield


def _ready_entry(display_name: str) -> ModelEntry:
    return ModelEntry(
        display_name=display_name,
        internal_id=display_name.lower().replace(" ", "_"),
        status=ModelHealth.READY,
        capabilities=ModelCapabilities(
            supports_batch=True,
            supports_cross_encoding="Cross-Encoder" in display_name,
            supports_explainability=True,
        ),
    )


@pytest.fixture(autouse=True)
def _mock_model_registry():
    """Mock model registry validation so strategy resolution works in CI.

    Without this, strategy resolution fails because model files (e.g.
    Cross-Encoder-Quora) are not available in CI environments.
    """
    with patch(
        "ares.orchestration.strategy_registry.find_entry",
        side_effect=lambda model_name, paths=None: _ready_entry(model_name),
    ):
        yield


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset rate limiter singleton between tests."""
    import ares.api.dependencies as deps

    deps._rate_limiter = None
    deps._security_manager = None
    yield


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """Disable rate limiting for all tests to avoid shared state."""
    settings = Settings()
    settings.rate_limit_enabled = False
    with patch.object(APIConfig, "get", return_value=settings):
        yield


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def test_client(app):
    return TestClient(app)


@pytest.fixture
def mock_engine():
    return _make_mock_engine()


@pytest.fixture
def auth_headers():
    manager = SecurityManager()
    token = manager.create_access_token("test-user", UserRole.USER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers():
    manager = SecurityManager()
    token = manager.create_access_token("test-admin", UserRole.ADMIN)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def grpc_service(mock_engine):
    with patch("ares._engine.ARES") as MockARES, patch("ares.ARES") as MockARES2:
        MockARES.return_value = mock_engine
        MockARES2.return_value = mock_engine
        from ares.grpc.services import AresGrpcService

        service = AresGrpcService()
        service._engine = mock_engine
        yield service


@pytest.fixture
def settings():
    return Settings()
