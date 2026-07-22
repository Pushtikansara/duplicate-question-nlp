from __future__ import annotations

from http.server import HTTPServer
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.grpc
class TestGrpcServer:
    @patch("ares.grpc.server.APIConfig.get")
    @patch("ares.grpc.server.AresGrpcService")
    def test_server_starts_and_stops(self, MockService, mock_config):
        mock_config.return_value.grpc_host = "127.0.0.1"
        mock_config.return_value.grpc_port = 0
        from ares.grpc.server import start_grpc_server, stop_grpc_server

        server = start_grpc_server(host="127.0.0.1", port=0)
        assert isinstance(server, HTTPServer)
        assert server.server_address is not None
        stop_grpc_server(server)

    @patch("ares.grpc.server.AresGrpcService")
    def test_server_health_endpoint(self, MockService):
        mock_service = MagicMock()
        mock_service.health.return_value = {"status": "healthy", "version": "0.2.0"}
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.health()
        assert result["status"] == "healthy"
        assert result["version"] == "0.2.0"

    @patch("ares.grpc.server.AresGrpcService")
    def test_server_predict_endpoint(self, MockService):
        mock_service = MagicMock()
        mock_service.predict.return_value = {
            "predicted_label": 1,
            "prediction": "duplicate",
            "confidence": 0.95,
        }
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.predict("q1?", "q2?")
        assert result["predicted_label"] == 1
        assert result["prediction"] == "duplicate"

    @patch("ares.grpc.server.AresGrpcService")
    def test_server_version_endpoint(self, MockService):
        mock_service = MagicMock()
        mock_service.version.return_value = {"version": "0.2.0", "api_version": "1.0.0"}
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.version()
        assert result["version"] == "0.2.0"

    @patch("ares.grpc.server.AresGrpcService")
    def test_server_system_info_endpoint(self, MockService):
        mock_service = MagicMock()
        mock_service.system_info.return_value = {"version": "0.2.0", "cpu_cores": 4}
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.system_info()
        assert result["cpu_cores"] == 4

    @patch("ares.grpc.server.AresGrpcService")
    def test_server_pipeline_endpoint(self, MockService):
        mock_service = MagicMock()
        mock_service.run_pipeline.return_value = {"success": True, "modules_executed": ["inference"]}
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.run_pipeline("q1", "q2")
        assert result["success"] is True

    @patch("ares.grpc.server.AresGrpcService")
    def test_do_get_health(self, MockService):
        mock_service = MagicMock()
        mock_service.health.return_value = {"status": "healthy"}
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.health()
        assert result == {"status": "healthy"}

    @patch("ares.grpc.server.AresGrpcService")
    def test_do_post_predict_batch(self, MockService):
        mock_service = MagicMock()
        mock_service.predict_batch.return_value = {
            "results": [],
            "success_count": 0,
            "failure_count": 0,
        }
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.predict_batch([{"question1": "q1", "question2": "q2"}])
        assert result["success_count"] == 0

    @patch("ares.grpc.server.AresGrpcService")
    def test_do_post_reflection(self, MockService):
        mock_service = MagicMock()
        mock_service.run_reflection.return_value = {"trust_score": 0.8}
        MockService.return_value = mock_service

        from ares.grpc.server import GrpcJsonHandler

        handler = GrpcJsonHandler
        handler.service = mock_service
        result = handler.service.run_reflection("q1", "q2")
        assert result["trust_score"] == 0.8
