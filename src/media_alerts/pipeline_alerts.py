"""Business decision for creator-facing media pipeline alerts."""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


class SmsSender(Protocol):
    def send(self, *, to: str, body: str, idempotency_key: str) -> str:
        raise AssertionError("protocol method")


class MediaJobEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    creator_phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    asset_title: str = Field(min_length=1, max_length=80)
    stage: Literal["asset_ingested", "processing_succeeded", "processing_failed"]


class AlertResult(BaseModel):
    action: Literal["recorded", "sent"]
    job_id: str
    message_id: str | None = None


def deliver_job_alert(event: MediaJobEvent, sender: SmsSender) -> AlertResult:
    if event.stage == "asset_ingested":
        return AlertResult(action="recorded", job_id=event.job_id)

    outcome = "ready for delivery" if event.stage == "processing_succeeded" else "needs review"
    body = f'Media job {event.job_id} for "{event.asset_title}" is {outcome}.'
    message_id = sender.send(
        to=event.creator_phone,
        body=body,
        idempotency_key=f"media-job:{event.job_id}:{event.stage}",
    )
    return AlertResult(action="sent", job_id=event.job_id, message_id=message_id)
