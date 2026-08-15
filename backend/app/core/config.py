from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Private Memory Map"
    api_prefix: str = "/api"
    gemma_model: str = "gemma4:e4b-128k"
    openrouter_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "PMM_OPENROUTER_API_KEY"),
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("OPENROUTER_BASE_URL", "PMM_OPENROUTER_BASE_URL"),
    )
    openrouter_model: str = Field(
        default="google/gemini-3.7-flash",
        validation_alias=AliasChoices("OPENROUTER_MODEL", "PMM_OPENROUTER_MODEL"),
    )
    database_url: str = "sqlite:///backend/local_data/private_memory_map.db"
    upload_dir: Path = Path("backend/local_data/uploads")
    frontend_dir: Path = Path("frontend/dist")
    max_upload_mb: int = 25
    allowed_image_types: tuple[str, ...] = Field(
        default=("image/jpeg", "image/png", "image/webp")
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    cors_origin_regex: str | None = r"http://(localhost|127\.0\.0\.1):\d+"
    workflow_temperature: float = 0
    workflow_num_ctx: int = 32768
    workflow_max_image_edge_px: int = 1280
    workflow_retry_invalid_json: int = 1
    workflow_max_qa_photos: int = 60
    auto_analyze_on_import: bool = True
    prompt_version: str = "travel-memory-v1"
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"
    reverse_proxy_user: str = Field(
        default="",
        validation_alias=AliasChoices("REVERSE_PROXY_USER", "PMM_REVERSE_PROXY_USER"),
    )
    reverse_proxy_password: str = Field(
        default="",
        validation_alias=AliasChoices(
            "REVERSE_PROXY_PASSWORD", "PMM_REVERSE_PROXY_PASSWORD"
        ),
    )
    enable_basic_auth: bool = False

    model_config = SettingsConfigDict(
        env_prefix="PMM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("s3_endpoint", mode="before")
    @classmethod
    def strip_s3_endpoint(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().rstrip("/")
        return value

    @property
    def database_kind(self) -> str:
        return self.database_url.split(":", maxsplit=1)[0]

    @property
    def s3_enabled(self) -> bool:
        return bool(
            self.s3_endpoint and self.s3_bucket and self.s3_access_key and self.s3_secret_key
        )

    @property
    def storage_kind(self) -> str:
        return "s3" if self.s3_enabled else "local"

    @property
    def basic_auth_enabled(self) -> bool:
        return bool(
            self.enable_basic_auth
            and self.reverse_proxy_user
            and self.reverse_proxy_password
        )

    def ensure_local_dirs(self) -> None:
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.replace("sqlite:///", "", 1))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.s3_enabled:
            self.upload_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
