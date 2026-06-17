from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudCostLab API"
    api_prefix: str = "/api"
    database_url: str = Field(
        default="postgresql+psycopg2://gaussdb:CloudGauss%402026@opengauss:5432/postgres"
    )
    cors_origins: list[str] | str = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:5173",
        ]
    )
    auto_seed: bool = True
    testing: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
