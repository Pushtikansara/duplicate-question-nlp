from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, cast

from ares.api.config import APIConfig
from ares.grpc.services import AresGrpcService

logger = logging.getLogger(__name__)


class GrpcJsonHandler(BaseHTTPRequestHandler):
    service = AresGrpcService()

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return cast("dict[str, Any]", json.loads(body))

    def do_POST(self) -> None:
        body = self._read_body()
        path = self.path.strip("/")
        try:
            if path == "predict":
                result = self.service.predict(
                    body.get("question1", ""),
                    body.get("question2", ""),
                    body.get("model"),
                    body.get("threshold"),
                    body.get("reflect"),
                )
                self._send_json(result)
            elif path == "predict_batch":
                result = self.service.predict_batch(body.get("requests", []))
                self._send_json(result)
            elif path == "health":
                self._send_json(self.service.health())
            elif path == "version":
                self._send_json(self.service.version())
            elif path == "system_info":
                self._send_json(self.service.system_info())
            elif path == "pipeline":
                result = self.service.run_pipeline(
                    body.get("question1", ""),
                    body.get("question2", ""),
                    body.get("enable_perception", True),
                    body.get("enable_routing", True),
                    body.get("enable_memory", True),
                    body.get("enable_semantic", True),
                    body.get("enable_reasoning", True),
                    body.get("enable_debate", True),
                )
                self._send_json(result)
            elif path == "reflection":
                result = self.service.run_reflection(
                    body.get("question1", ""),
                    body.get("question2", ""),
                    body.get("prediction"),
                )
                self._send_json(result)
            elif path == "memory_search":
                entries = self.service.search_memory(
                    body.get("query", ""),
                    body.get("limit", 10),
                    body.get("memory_type"),
                )
                self._send_json({"entries": entries})
            elif path == "plugins":
                self._send_json({"plugins": self.service.list_plugins()})
            else:
                self._send_json({"error": f"Unknown method: {path}"}, 404)
        except Exception as e:
            logger.exception("gRPC handler error for %s", path)
            self._send_json({"error": str(e)}, 500)

    def do_GET(self) -> None:
        path = self.path.strip("/")
        if path == "health":
            self._send_json(self.service.health())
        elif path == "version":
            self._send_json(self.service.version())
        else:
            self._send_json({"error": f"Unknown endpoint: {path}"}, 404)

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("gRPC JSON: %s", format % args)


def start_grpc_server(
    host: str | None = None,
    port: int | None = None,
) -> HTTPServer:
    config = APIConfig.get()
    host = host or config.grpc_host
    port = port or config.grpc_port
    server = HTTPServer((host, port), GrpcJsonHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("gRPC JSON server listening on %s:%s", host, port)
    return server


def stop_grpc_server(server: HTTPServer) -> None:
    server.shutdown()
    logger.info("gRPC JSON server stopped")
