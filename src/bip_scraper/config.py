from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BIP_", extra="ignore")

    mattermost_mode: Literal["disabled", "webhook", "api"] = "disabled"
    mattermost_webhook_url: AnyHttpUrl | None = None
    mattermost_api_url: AnyHttpUrl | None = None
    mattermost_token: str | None = None
    mattermost_channel_id: str | None = None
    request_timeout_seconds: float = Field(default=20.0, gt=0)
    max_retries: int = Field(default=3, ge=0)

    @model_validator(mode="after")
    def validate_mattermost(self) -> Settings:
        if self.mattermost_mode == "webhook" and self.mattermost_webhook_url is None:
            raise ValueError("BIP_MATTERMOST_WEBHOOK_URL is required when mode=webhook")
        if self.mattermost_mode == "api":
            if self.mattermost_api_url is None:
                raise ValueError("BIP_MATTERMOST_API_URL is required when mode=api")
            if not self.mattermost_token:
                raise ValueError("BIP_MATTERMOST_TOKEN is required when mode=api")
            if not self.mattermost_channel_id:
                raise ValueError("BIP_MATTERMOST_CHANNEL_ID is required when mode=api")
        return self
