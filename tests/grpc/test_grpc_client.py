from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from urllib.request import Request

import pytest


@pytest.mark.grpc
class TestGrpcClient:
    def test_client_initializes_with_host_and_port(self):
        from ares.grpc.client import GrpcClient

        client = GrpcClient("localhost", 50051)
        assert client._base_url == "http://localhost:50051"

    def test_client_default_host_and_port(self):
        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        assert client._base_url == "http://localhost:50051"

    @patch("ares.grpc.client.urlopen")
    def test_client_health_returns_dict(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"status": "healthy"}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.health()
        assert result == {"status": "healthy"}

    @patch("ares.grpc.client.urlopen")
    def test_client_predict_returns_dict(self, mock_urlopen):
        expected = {"predicted_label": 1, "prediction": "duplicate", "confidence": 0.95}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.predict("q1?", "q2?")
        assert result["predicted_label"] == 1

    @patch("ares.grpc.client.urlopen")
    def test_client_version_returns_dict(self, mock_urlopen):
        expected = {"version": "0.2.0", "api_version": "1.0.0"}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.version()
        assert result["version"] == "0.2.0"

    @patch("ares.grpc.client.urlopen")
    def test_client_system_info_returns_dict(self, mock_urlopen):
        expected = {"version": "0.2.0", "cpu_cores": 4}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.system_info()
        assert result["cpu_cores"] == 4

    @patch("ares.grpc.client.urlopen")
    def test_client_predict_batch_returns_dict(self, mock_urlopen):
        expected = {"results": [], "success_count": 0, "failure_count": 0}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.predict_batch([{"question1": "q1", "question2": "q2"}])
        assert result["success_count"] == 0

    @patch("ares.grpc.client.urlopen")
    def test_client_run_pipeline_returns_dict(self, mock_urlopen):
        expected = {"success": True, "modules_executed": ["inference"]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.run_pipeline("q1", "q2")
        assert result["success"] is True

    @patch("ares.grpc.client.urlopen")
    def test_client_run_reflection_returns_dict(self, mock_urlopen):
        expected = {"trust_score": 0.8, "trust_level": "high"}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.run_reflection("q1", "q2")
        assert result["trust_score"] == 0.8

    @patch("ares.grpc.client.urlopen")
    def test_client_search_memory_returns_dict(self, mock_urlopen):
        expected = {"entries": []}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.search_memory("test")
        assert result == {"entries": []}

    @patch("ares.grpc.client.urlopen")
    def test_client_list_plugins_returns_dict(self, mock_urlopen):
        expected = {"plugins": []}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(expected).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.list_plugins()
        assert result == {"plugins": []}

    @patch("ares.grpc.client.urlopen")
    def test_client_sends_post_for_predict(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"predicted_label": 1}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        client.predict("q1", "q2")
        call_args = mock_urlopen.call_args
        assert call_args is not None
        request = call_args[0][0]
        assert isinstance(request, Request)
        assert "predict" in request.get_full_url()

    @patch("ares.grpc.client.urlopen")
    def test_client_sends_get_for_health(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"status": "healthy"}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        client.health()
        call_args = mock_urlopen.call_args
        assert call_args is not None
        request = call_args[0][0]
        assert request.method == "GET"

    @patch("ares.grpc.client.urlopen")
    def test_client_sends_post_for_predict_batch(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"results": []}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        client.predict_batch([{"question1": "q1", "question2": "q2"}])
        call_args = mock_urlopen.call_args
        assert call_args is not None
        request = call_args[0][0]
        assert "predict_batch" in request.get_full_url()

    @patch("ares.grpc.client.urlopen")
    def test_client_error_returns_error_dict(self, mock_urlopen):
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Connection refused")

        from ares.grpc.client import GrpcClient

        client = GrpcClient()
        result = client.health()
        assert "error" in result
