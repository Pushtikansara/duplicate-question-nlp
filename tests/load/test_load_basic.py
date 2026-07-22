from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest


@pytest.mark.load
class TestSequentialLoad:
    def test_sequential_predict_throughput(self, test_client, auth_headers):
        payload = {"question1": "What is Python?", "question2": "What is Java?"}
        count = 10
        start = time.time()
        for _ in range(count):
            response = test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
            assert response.status_code == 200
        elapsed = time.time() - start
        throughput = count / elapsed
        assert throughput > 0

    def test_sequential_predict_all_succeed(self, test_client, auth_headers):
        payload = {"question1": "q1?", "question2": "q2?"}
        for _ in range(20):
            response = test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
            assert response.status_code == 200

    def test_sequential_batch_throughput(self, test_client, auth_headers):
        payload = {"pairs": [["q1?", "q2?"], ["q3?", "q4?"]]}
        start = time.time()
        for _ in range(10):
            response = test_client.post("/api/v1/predict/batch", json=payload, headers=auth_headers)
            assert response.status_code == 200
        elapsed = time.time() - start
        assert elapsed > 0


@pytest.mark.load
class TestConcurrentLoad:
    def test_concurrent_predict_requests(self, test_client, auth_headers):
        payload = {"question1": "q1?", "question2": "q2?"}

        def send_request():
            return test_client.post("/api/v1/predict", json=payload, headers=auth_headers)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_request) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]
        assert all(r.status_code == 200 for r in results)

    def test_concurrent_batch_requests(self, test_client, auth_headers):
        payload = {"pairs": [["q1?", "q2?"]]}

        def send_batch():
            return test_client.post("/api/v1/predict/batch", json=payload, headers=auth_headers)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_batch) for _ in range(6)]
            results = [f.result() for f in as_completed(futures)]
        assert all(r.status_code == 200 for r in results)

    def test_concurrent_health_requests(self, test_client):
        def send_health():
            return test_client.get("/api/v1/health")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(send_health) for _ in range(8)]
            results = [f.result() for f in as_completed(futures)]
        assert all(r.status_code == 200 for r in results)

    def test_concurrent_mixed_requests(self, test_client, auth_headers):
        def do_predict():
            return test_client.post(
                "/api/v1/predict",
                json={"question1": "a", "question2": "b"},
                headers=auth_headers,
            )

        def do_health():
            return test_client.get("/api/v1/health")

        with ThreadPoolExecutor(max_workers=4) as executor:
            pred_futures = [executor.submit(do_predict) for _ in range(5)]
            health_futures = [executor.submit(do_health) for _ in range(5)]
            all_futures = pred_futures + health_futures
            results = [f.result() for f in as_completed(all_futures)]
        assert all(r.status_code == 200 for r in results)


@pytest.mark.load
class TestLoadResponseTimes:
    def test_predict_response_time(self, test_client, auth_headers):
        payload = {"question1": "q1?", "question2": "q2?"}
        times = []
        for _ in range(5):
            start = time.time()
            test_client.post("/api/v1/predict", json=payload, headers=auth_headers)
            times.append((time.time() - start) * 1000)
        avg = sum(times) / len(times)
        assert avg < 5000
