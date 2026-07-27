from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARES_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    log_level: str = "info"

    # API
    api_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = ["*"]
    trusted_hosts: list[str] = ["*"]
    max_request_size_mb: int = 50
    request_timeout_seconds: int = 120

    # Security
    secret_key: str = ""
    api_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    api_key_header: str = "X-API-Key"
    bcrypt_rounds: int = 12

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_burst: int = 20

    # Observability
    otel_service_name: str = "ares-api"
    otel_endpoint: str = ""
    prometheus_enabled: bool = True
    metrics_prefix: str = "ares_"

    # Storage
    data_dir: str = ""
    upload_dir: str = "/tmp/ares/uploads"
    max_upload_size_mb: int = 200

    # gRPC
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    grpc_max_workers: int = 10
    grpc_max_message_length_mb: int = 100

    # Model
    default_model: str = ""
    default_threshold: float = 0.5
    enable_reflection: bool = True
    enable_pipeline: bool = True
    model_cache_ttl_seconds: int = 300


class APIConfig:
    _instance: APIConfig | None = None

    def __init__(self) -> None:
        self.settings = Settings()

    @classmethod
    def get(cls) -> Settings:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance.settings

    @classmethod
    def reload(cls) -> Settings:
        cls._instance = cls()
        return cls._instance.settings
