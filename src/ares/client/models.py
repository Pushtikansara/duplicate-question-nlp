from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PredictionRequest:
    question1: str
    question2: str
    model: str | None = None
    threshold: float | None = None
    reflect: bool | None = None


@dataclass
class PredictionResponse:
    question1: str
    question2: str
    predicted_label: int
    prediction: str
    prob_duplicate: float
    prob_non_duplicate: float
    confidence: float
    threshold: float
    model_label: str
    latency_ms: float
    trust_score: float | None = None
    trust_level: str | None = None
    risk_level: str | None = None
    request_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PredictionResponse:
        return cls(
            question1=data.get("question1", ""),
            question2=data.get("question2", ""),
            predicted_label=data.get("predicted_label", 0),
            prediction=data.get("prediction", "unknown"),
            prob_duplicate=data.get("prob_duplicate", 0.0),
            prob_non_duplicate=data.get("prob_non_duplicate", 0.0),
            confidence=data.get("confidence", 0.0),
            threshold=data.get("threshold", 0.5),
            model_label=data.get("model_label", ""),
            latency_ms=data.get("latency_ms", 0.0),
            trust_score=data.get("trust_score"),
            trust_level=data.get("trust_level"),
            risk_level=data.get("risk_level"),
            request_id=data.get("request_id", ""),
        )


@dataclass
class BatchPredictionResponse:
    results: list[PredictionResponse]
    total_latency_ms: float
    average_latency_ms: float
    success_count: int
    failure_count: int
    request_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchPredictionResponse:
        results = [PredictionResponse.from_dict(r) for r in data.get("results", [])]
        return cls(
            results=results,
            total_latency_ms=data.get("total_latency_ms", 0.0),
            average_latency_ms=data.get("average_latency_ms", 0.0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            request_id=data.get("request_id", ""),
        )


@dataclass
class HealthResponse:
    status: str
    version: str
    uptime_seconds: float
    components: dict[str, str]
    request_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthResponse:
        return cls(
            status=data.get("status", "unknown"),
            version=data.get("version", ""),
            uptime_seconds=data.get("uptime_seconds", 0.0),
            components=data.get("components", {}),
            request_id=data.get("request_id", ""),
        )


@dataclass
class VersionResponse:
    version: str
    python_version: str
    platform: str
    api_version: str
    request_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VersionResponse:
        return cls(
            version=data.get("version", ""),
            python_version=data.get("python_version", ""),
            platform=data.get("platform", ""),
            api_version=data.get("api_version", ""),
            request_id=data.get("request_id", ""),
        )


@dataclass
class SystemInfoResponse:
    version: str
    python_version: str
    platform: str
    cpu_cores: int
    memory_gb: float
    gpu_available: bool
    gpu_name: str | None = None
    cuda_version: str | None = None
    torch_version: str = ""
    request_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemInfoResponse:
        return cls(
            version=data.get("version", ""),
            python_version=data.get("python_version", ""),
            platform=data.get("platform", ""),
            cpu_cores=data.get("cpu_cores", 0),
            memory_gb=data.get("memory_gb", 0.0),
            gpu_available=data.get("gpu_available", False),
            gpu_name=data.get("gpu_name"),
            cuda_version=data.get("cuda_version"),
            torch_version=data.get("torch_version", ""),
            request_id=data.get("request_id", ""),
        )
