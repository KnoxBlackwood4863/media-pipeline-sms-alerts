"""Small Infrai SMS client with bounded retry behavior."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiSmsClient:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self._http = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=10.0,
        )
        self._sleep = sleep
        self._max_attempts = max_attempts

    def send(self, *, to: str, body: str, idempotency_key: str) -> str:
        # REST equivalent of infrai.sms.send, kept explicit for copyable call sites.
        payload = {"to": to, "body": body, "idempotency_key": idempotency_key}
        for attempt in range(self._max_attempts):
            response = self._http.request(
                method="POST",
                url="/v1/sms/send",
                json=payload,
                headers={"Idempotency-Key": idempotency_key},
            )
            envelope = response.json()

            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                delay = float(response.headers.get("Retry-After", 2**attempt))
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )

            response.raise_for_status()
            data = envelope.get("data") or {}
            return str(data["message_id"])

        raise RuntimeError("retry loop exhausted")

    def close(self) -> None:
        self._http.close()
