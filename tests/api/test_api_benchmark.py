from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.api
class TestBenchmarkEndpoint:
    def test_list_benchmarks_returns_list(self, test_client, admin_auth_headers):
        with patch("duplicate_question_app._evaluation.benchmark_runner.BenchmarkRunner") as MockBR:
            instance = MagicMock()
            instance.list_results.return_value = []
            MockBR.return_value = instance
            response = test_client.get("/api/v1/benchmark", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_benchmarks_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/v1/benchmark")
        assert response.status_code == 401

    def test_list_benchmarks_with_user_returns_403(self, test_client, auth_headers):
        response = test_client.get("/api/v1/benchmark", headers=auth_headers)
        assert response.status_code == 403


@pytest.mark.api
class TestBenchmarkRunEndpoint:
    def test_run_benchmark_returns_200(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "test-benchmark", "epochs": 1},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_run_benchmark_returns_name(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "my-bench", "epochs": 1},
            headers=admin_auth_headers,
        )
        data = response.json()
        assert data["name"] == "my-bench"

    def test_run_benchmark_returns_status(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "test", "epochs": 1},
            headers=admin_auth_headers,
        )
        data = response.json()
        assert data["status"] == "completed"

    def test_run_benchmark_returns_metrics(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "test", "epochs": 1},
            headers=admin_auth_headers,
        )
        data = response.json()
        assert "metrics" in data
        assert isinstance(data["metrics"], dict)

    def test_run_benchmark_returns_model(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "test", "epochs": 1, "model": "test-model"},
            headers=admin_auth_headers,
        )
        data = response.json()
        assert data["model"] == "test-model"

    def test_run_benchmark_returns_total_latency(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "test", "epochs": 1},
            headers=admin_auth_headers,
        )
        data = response.json()
        assert "total_latency_ms" in data

    def test_run_benchmark_returns_request_id(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "test", "epochs": 1},
            headers=admin_auth_headers,
        )
        data = response.json()
        assert "request_id" in data

    def test_run_benchmark_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/benchmark/run", json={"name": "test", "epochs": 1})
        assert response.status_code == 401

    def test_run_benchmark_metrics_contains_latency(self, test_client, admin_auth_headers):
        response = test_client.post(
            "/api/v1/benchmark/run",
            json={"name": "test", "epochs": 1},
            headers=admin_auth_headers,
        )
        data = response.json()
        metrics = data["metrics"]
        assert "avg_latency_ms" in metrics or "p50_latency_ms" in metrics
