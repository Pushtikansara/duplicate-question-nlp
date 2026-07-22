from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest


@pytest.mark.performance
class TestPredictLatency:
    LATENCY_THRESHOLD_MS = 1000

    def test_single_predict_latency(self, test_client, auth_headers):
        payload = {"question1": "What is Python?", "question2": "What is Java?"}
        start = time.perf_counter()
        response = test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        assert elapsed_ms < self.LATENCY_THRESHOLD_MS

    def test_predict_latency_under_threshold(self, test_client, auth_headers):
        payload = {"question1": "a", "question2": "b"}
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
            latencies.append((time.perf_counter() - start) * 1000)
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < self.LATENCY_THRESHOLD_MS

    def test_batch_predict_latency(self, test_client, auth_headers):
        payload = {"pairs": [["q1?", "q2?"], ["q3?", "q4?"], ["q5?", "q6?"]]}
        start = time.perf_counter()
        response = test_client.post("/api/v1/predict/batch", json=payload, headers=auth_headers)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        assert elapsed_ms < self.LATENCY_THRESHOLD_MS

    def test_health_latency(self, test_client):
        start = time.perf_counter()
        response = test_client.get("/api/v1/health")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        assert elapsed_ms < self.LATENCY_THRESHOLD_MS

    def test_percentile_latency_measurement(self, test_client, auth_headers):
        payload = {"question1": "a", "question2": "b"}
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
            latencies.append((time.perf_counter() - start) * 1000)
        sorted_lat = sorted(latencies)
        p50 = sorted_lat[len(sorted_lat) // 2]
        p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
        assert p50 < self.LATENCY_THRESHOLD_MS
        assert p95 < self.LATENCY_THRESHOLD_MS

    def test_predict_returns_latency_in_response(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/predict",
            json={"question1": "a", "question2": "b"},
            headers=auth_headers,
        )
        data = response.json()
        assert "latency_ms" in data
        assert isinstance(data["latency_ms"], float)

    def test_concurrent_predict_latency(self, test_client, auth_headers):
        payload = {"question1": "a", "question2": "b"}

        def send():
            start = time.perf_counter()
            test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
            return (time.perf_counter() - start) * 1000

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [ex.submit(send) for _ in range(8)]
            latencies = [f.result() for f in as_completed(futures)]
        avg = sum(latencies) / len(latencies)
        assert avg < self.LATENCY_THRESHOLD_MS

    def test_grpc_predict_latency(self, grpc_service):
        start = time.perf_counter()
        result = grpc_service.predict("q1", "q2")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert "predicted_label" in result
        assert elapsed_ms < self.LATENCY_THRESHOLD_MS

    def test_prediction_latency_consistency(self, test_client, auth_headers):
        payload = {"question1": "a", "question2": "b"}
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
            latencies.append((time.perf_counter() - start) * 1000)
        variance = max(latencies) - min(latencies)
        assert variance < self.LATENCY_THRESHOLD_MS
