from __future__ import annotations

import httpx


def post_via_webhook(*, webhook_url: str, message: str, timeout_seconds: float) -> None:
    response = httpx.post(
        webhook_url,
        json={"text": message},
        timeout=timeout_seconds,
    )
    response.raise_for_status()


def post_via_api(
    *,
    api_base_url: str,
    token: str,
    channel_id: str,
    message: str,
    timeout_seconds: float,
) -> None:
    response = httpx.post(
        f"{api_base_url.rstrip('/')}/api/v4/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel_id": channel_id, "message": message},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
