from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.api
class TestMemoryEndpoint:
    def test_get_memory_returns_list(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager") as MockMM:
            instance = MagicMock()
            instance.list.return_value = []
            MockMM.return_value = instance
            response = test_client.get("/api/v1/memory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_memory_accepts_limit_param(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager") as MockMM:
            instance = MagicMock()
            instance.list.return_value = []
            MockMM.return_value = instance
            response = test_client.get("/api/v1/memory?limit=5", headers=auth_headers)
        assert response.status_code == 200

    def test_get_memory_accepts_type_param(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager") as MockMM:
            instance = MagicMock()
            instance.list.return_value = []
            MockMM.return_value = instance
            response = test_client.get("/api/v1/memory?memory_type=inference", headers=auth_headers)
        assert response.status_code == 200

    def test_get_memory_returns_empty_list_when_no_entries(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager") as MockMM:
            instance = MagicMock()
            instance.list.return_value = []
            MockMM.return_value = instance
            response = test_client.get("/api/v1/memory", headers=auth_headers)
        assert response.json() == []

    def test_get_memory_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/v1/memory")
        assert response.status_code == 401


@pytest.mark.api
class TestMemorySearchEndpoint:
    def test_memory_search_returns_results(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager") as MockMM:
            instance = MagicMock()
            instance.search.return_value = []
            MockMM.return_value = instance
            response = test_client.post(
                "/api/v1/memory/search",
                json={"query": "test query", "limit": 5},
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_memory_search_with_query(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager") as MockMM:
            instance = MagicMock()
            instance.search.return_value = []
            MockMM.return_value = instance
            response = test_client.post(
                "/api/v1/memory/search",
                json={"query": "python", "limit": 10},
                headers=auth_headers,
            )
        assert response.status_code == 200

    def test_memory_search_empty_query_returns_422(self, test_client, auth_headers):
        response = test_client.post(
            "/api/v1/memory/search",
            json={"query": "", "limit": 10},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_memory_search_without_auth_returns_401(self, test_client):
        response = test_client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 10},
        )
        assert response.status_code == 401

    def test_memory_search_returns_memory_entries_with_fields(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_manager.MemoryManager") as MockMM:
            instance = MagicMock()
            mock_entry = MagicMock()
            mock_entry.id = "1"
            mock_entry.type = "inference"
            mock_entry.content = {"key": "value"}
            mock_entry.confidence = 0.9
            mock_entry.created_at = __import__("datetime").datetime(2024, 1, 1)
            mock_entry.last_accessed = __import__("datetime").datetime(2024, 1, 1)
            mock_entry.access_count = 5
            mock_entry.tags = ["test"]
            instance.search.return_value = [mock_entry]
            MockMM.return_value = instance
            response = test_client.post(
                "/api/v1/memory/search",
                json={"query": "test", "limit": 10},
                headers=auth_headers,
            )
        data = response.json()
        assert len(data) == 1
        entry = data[0]
        assert "id" in entry
        assert "type" in entry
        assert "content" in entry
        assert "confidence" in entry


@pytest.mark.api
class TestMemoryStatsEndpoint:
    def test_memory_stats_returns_dict(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_statistics.MemoryStatistics") as MockMS:
            instance = MagicMock()
            instance.get_stats.return_value = {"total": 10}
            MockMS.return_value = instance
            response = test_client.get("/api/v1/memory/stats", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_memory_stats_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/v1/memory/stats")
        assert response.status_code == 401


@pytest.mark.api
class TestMemoryCleanEndpoint:
    def test_memory_clean_returns_ok(self, test_client, auth_headers):
        with patch("duplicate_question_app._memory.memory_consolidator.MemoryConsolidator") as MockMC:
            instance = MagicMock()
            instance.consolidate.return_value = {"cleaned": 5}
            MockMC.return_value = instance
            response = test_client.post("/api/v1/memory/clean", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_memory_clean_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/v1/memory/clean")
        assert response.status_code == 401
