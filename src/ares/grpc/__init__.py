from __future__ import annotations

from ares.grpc.authentication import GrpcAuthInterceptor
from ares.grpc.client import GrpcClient
from ares.grpc.compression import compress, decompress
from ares.grpc.interceptors import LoggingInterceptor
from ares.grpc.reflection import get_grpc_reflection
from ares.grpc.server import GrpcJsonHandler, start_grpc_server, stop_grpc_server
from ares.grpc.services import AresGrpcService
from ares.grpc.streaming import stream_predictions

__all__ = [
    "start_grpc_server",
    "stop_grpc_server",
    "GrpcJsonHandler",
    "GrpcClient",
    "AresGrpcService",
    "LoggingInterceptor",
    "GrpcAuthInterceptor",
    "get_grpc_reflection",
    "compress",
    "decompress",
    "stream_predictions",
]
